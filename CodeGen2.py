#!/usr/bin/env python3
"""CodeGen2: open-source multimodal RTL fine-tuning pipeline.

No proprietary API keys are used. Install the ML stack only when training:
  pip install torch transformers datasets peft accelerate pillow
Optional 4-bit QLoRA support:
  pip install bitsandbytes

Typical flow:
  python CodeGen2.py prepare --runs runs --output dataset
  python CodeGen2.py train --dataset dataset --base-model <HF vision-language model>
  python CodeGen2.py infer --adapter training/adapter --image diagram.png --instruction "Write Verilog"
  python CodeGen2.py evaluate --predictions predictions.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MODEL = "Qwen/Qwen2.5-VL-3B-Instruct"
HDL_EXTENSIONS = {"verilog": ".v", "systemverilog": ".sv", "vhdl": ".vhd"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{number}: each JSONL line must be an object")
            rows.append(value)
    return rows


def first_text(record: dict[str, Any], *names: str) -> str:
    for name in names:
        value = record.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def code_from_record(record: dict[str, Any], record_path: Path) -> str:
    code = first_text(record, "generated_code", "code", "target_code", "rtl")
    if code:
        return code
    relative = first_text(record, "generated_code_path", "code_path")
    if relative:
        candidate = (record_path.parent / relative).resolve()
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8", errors="replace")
    return ""


def resolve_image(record: dict[str, Any], record_path: Path) -> Path | None:
    raw = first_text(record, "image_path", "image")
    if not raw:
        source = record.get("source")
        if isinstance(source, dict):
            raw = first_text(source, "image_path", "image")
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = record_path.parent / candidate
    return candidate.resolve() if candidate.is_file() else None


def find_records(source: Path) -> list[tuple[Path, dict[str, Any]]]:
    if source.is_file() and source.suffix.lower() == ".jsonl":
        return [(source, row) for row in read_jsonl(source)]
    if source.is_file() and source.suffix.lower() == ".json":
        value = read_json(source)
        return [(source, value)] if isinstance(value, dict) else []
    if not source.is_dir():
        raise FileNotFoundError(f"Record source does not exist: {source}")
    found: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(source.rglob("result.json")):
        try:
            value = read_json(path)
            if isinstance(value, dict):
                found.append((path, value))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warning: skipped unreadable record {path}: {exc}", file=sys.stderr)
    return found


def normalized_language(value: str) -> str:
    value = value.lower().strip()
    aliases = {"sv": "systemverilog", "verilog": "verilog", "v": "verilog", "vhdl": "vhdl", "vhd": "vhdl"}
    return aliases.get(value, "unknown")


def build_target(analysis: str, code: str, language: str) -> str:
    explanation = analysis or "The diagram and instruction describe the requested hardware behaviour."
    fence = "systemverilog" if language == "systemverilog" else language
    return f"Image analysis:\n{explanation}\n\nGenerated RTL:\n```{fence}\n{code.strip()}\n```"


def split_for(identifier: str, validation_percent: int) -> str:
    value = int(hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:8], 16) % 100
    return "validation" if value < validation_percent else "train"


def cmd_prepare(args: argparse.Namespace) -> int:
    source, output = Path(args.runs).resolve(), Path(args.output).resolve()
    records = find_records(source)
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    copied_images = output / "images"

    for ordinal, (record_path, record) in enumerate(records):
        if record.get("approved") is not True:
            excluded.append({"record": str(record_path), "reason": "not approved"})
            continue
        image = resolve_image(record, record_path)
        instruction = first_text(record, "instruction", "prompt")
        analysis = first_text(record, "image_analysis", "analysis", "explanation")
        code = code_from_record(record, record_path)
        language = normalized_language(first_text(record, "language"))
        if image is None:
            excluded.append({"record": str(record_path), "reason": "image missing"})
        elif not instruction:
            excluded.append({"record": str(record_path), "reason": "instruction missing"})
        elif not code:
            excluded.append({"record": str(record_path), "reason": "generated HDL missing"})
        elif language == "unknown":
            excluded.append({"record": str(record_path), "reason": "HDL language missing or unsupported"})
        else:
            identifier = first_text(record, "id", "run_id") or hashlib.sha256(
                f"{record_path}:{ordinal}".encode("utf-8")
            ).hexdigest()[:16]
            image_path = image
            if args.copy_images:
                copied_images.mkdir(parents=True, exist_ok=True)
                destination = copied_images / f"{identifier}{image.suffix.lower()}"
                if not destination.exists():
                    shutil.copy2(image, destination)
                image_path = destination
            accepted.append({
                "id": identifier,
                "image": str(image_path),
                "instruction": instruction,
                "target": build_target(analysis, code, language),
                "language": language,
                "verification": record.get("verification", {}),
                "source": {"record": str(record_path)},
                "split": split_for(identifier, args.validation_percent),
            })

    train = [entry for entry in accepted if entry["split"] == "train"]
    validation = [entry for entry in accepted if entry["split"] == "validation"]
    write_jsonl(output / "train.jsonl", train)
    write_jsonl(output / "validation.jsonl", validation)
    write_json(output / "manifest.json", {
        "created_at": now(), "source": str(source), "validation_percent": args.validation_percent,
        "included": len(accepted), "train": len(train), "validation": len(validation),
        "excluded": excluded, "copy_images": args.copy_images,
    })
    print(f"Prepared {len(accepted)} examples: {len(train)} train, {len(validation)} validation")
    print(f"Dataset manifest: {output / 'manifest.json'}")
    return 0


def require_ml() -> tuple[Any, Any, Any, Any, Any, Any]:
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, PeftModel, get_peft_model
        from transformers import AutoModelForVision2Seq, AutoProcessor, Trainer, TrainingArguments
        return torch, Dataset, (LoraConfig, PeftModel, get_peft_model), AutoModelForVision2Seq, AutoProcessor, (Trainer, TrainingArguments)
    except ImportError as exc:
        raise RuntimeError(
            "Training/inference dependencies are missing. Install: "
            "pip install torch transformers datasets peft accelerate pillow"
        ) from exc


def dependency_status() -> dict[str, bool]:
    import importlib.util
    return {name: importlib.util.find_spec(name) is not None for name in ("torch", "transformers", "datasets", "peft", "PIL", "bitsandbytes")}


def cmd_train(args: argparse.Namespace) -> int:
    dataset_dir, output_dir = Path(args.dataset).resolve(), Path(args.output).resolve()
    train_rows = read_jsonl(dataset_dir / "train.jsonl")
    validation_path = dataset_dir / "validation.jsonl"
    validation_rows = read_jsonl(validation_path) if validation_path.exists() else []
    if not train_rows:
        raise ValueError("Training dataset is empty. Approve and prepare examples first.")
    if args.dry_run:
        print(json.dumps({"base_model": args.base_model, "train_examples": len(train_rows), "validation_examples": len(validation_rows), "dependencies": dependency_status()}, indent=2))
        return 0

    torch, Dataset, peft, ModelClass, ProcessorClass, trainer_classes = require_ml()
    LoraConfig, _, get_peft_model = peft
    Trainer, TrainingArguments = trainer_classes
    from PIL import Image

    model_options: dict[str, Any] = {"trust_remote_code": args.trust_remote_code}
    quantized = False
    if args.qlora:
        try:
            from transformers import BitsAndBytesConfig
            if not torch.cuda.is_available():
                raise RuntimeError("--qlora requires a CUDA-capable GPU")
            model_options["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
            model_options["device_map"] = "auto"
            quantized = True
        except ImportError as exc:
            raise RuntimeError("--qlora requires bitsandbytes: pip install bitsandbytes") from exc
    elif torch.cuda.is_available():
        model_options["torch_dtype"] = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16

    processor = ProcessorClass.from_pretrained(args.base_model, trust_remote_code=args.trust_remote_code)
    model = ModelClass.from_pretrained(args.base_model, **model_options)
    lora = LoraConfig(r=args.lora_rank, lora_alpha=args.lora_rank * 2, lora_dropout=0.05,
                      bias="none", task_type="CAUSAL_LM", target_modules="all-linear")
    model = get_peft_model(model, lora)

    class CircuitDataset(torch.utils.data.Dataset):
        def __init__(self, rows: list[dict[str, Any]]): self.rows = rows
        def __len__(self) -> int: return len(self.rows)
        def __getitem__(self, index: int) -> dict[str, Any]:
            row = self.rows[index]
            image = Image.open(row["image"]).convert("RGB")
            prompt = f"<image>\nInstruction: {row['instruction']}\nRespond with an image analysis and synthesizable RTL.\n"
            encoded = processor(text=prompt + row["target"], images=image, return_tensors="pt", truncation=True, max_length=args.max_length)
            result = {key: value.squeeze(0) for key, value in encoded.items()}
            result["labels"] = result["input_ids"].clone()  # broad compatibility across VLM processors
            return result

    def collate(features: list[dict[str, Any]]) -> dict[str, Any]:
        keys = set().union(*(feature.keys() for feature in features))
        return {key: torch.stack([feature[key] for feature in features]) for key in keys if all(key in feature for feature in features)}

    output_dir.mkdir(parents=True, exist_ok=True)
    training_args = TrainingArguments(
        output_dir=str(output_dir), num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation, learning_rate=args.learning_rate,
        logging_steps=1, save_strategy="epoch", report_to=[], remove_unused_columns=False,
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=CircuitDataset(train_rows),
                      eval_dataset=CircuitDataset(validation_rows) if validation_rows else None,
                      data_collator=collate)
    trainer.train()
    adapter_dir = output_dir / "adapter"
    model.save_pretrained(adapter_dir)
    processor.save_pretrained(adapter_dir)
    write_json(output_dir / "training_run.json", {
        "completed_at": now(), "base_model": args.base_model, "adapter": str(adapter_dir),
        "train_examples": len(train_rows), "validation_examples": len(validation_rows),
        "qlora": quantized, "lora_rank": args.lora_rank, "epochs": args.epochs,
        "batch_size": args.batch_size, "gradient_accumulation": args.gradient_accumulation,
        "learning_rate": args.learning_rate, "cuda": torch.cuda.is_available(),
    })
    print(f"Adapter saved to: {adapter_dir}")
    return 0


def cmd_infer(args: argparse.Namespace) -> int:
    image = Path(args.image).resolve()
    if not image.is_file():
        raise FileNotFoundError(f"Image not found: {image}")
    torch, _, peft, ModelClass, ProcessorClass, _ = require_ml()
    _, PeftModel, _ = peft
    from PIL import Image
    adapter = Path(args.adapter).resolve()
    metadata = read_json(adapter.parent / "training_run.json") if (adapter.parent / "training_run.json").exists() else {}
    base_model = args.base_model or metadata.get("base_model")
    if not base_model:
        raise ValueError("Pass --base-model or keep adapter beside training_run.json")
    processor = ProcessorClass.from_pretrained(adapter if (adapter / "processor_config.json").exists() else base_model, trust_remote_code=args.trust_remote_code)
    model = PeftModel.from_pretrained(ModelClass.from_pretrained(base_model, trust_remote_code=args.trust_remote_code), adapter)
    model.eval()
    prompt = f"<image>\nInstruction: {args.instruction}\nProvide image analysis, then synthesizable RTL."
    inputs = processor(text=prompt, images=Image.open(image).convert("RGB"), return_tensors="pt")
    if torch.cuda.is_available(): inputs = {key: value.to(model.device) for key, value in inputs.items()}
    with torch.no_grad(): output = model.generate(**inputs, max_new_tokens=args.max_new_tokens)
    answer = processor.batch_decode(output, skip_special_tokens=True)[0]
    fenced = re.search(r"```(?:verilog|systemverilog|vhdl)?\s*(.*?)```", answer, re.DOTALL | re.IGNORECASE)
    result = {"created_at": now(), "image": str(image), "instruction": args.instruction, "base_model": base_model,
              "adapter": str(adapter), "answer": answer, "generated_code": fenced.group(1).strip() if fenced else ""}
    if args.output: write_json(Path(args.output).resolve(), result)
    print(json.dumps(result, indent=2))
    return 0


def compiler_check(code: str, language: str, testbench: str = "") -> dict[str, Any]:
    language = normalized_language(language)
    tool = "iverilog" if language in {"verilog", "systemverilog"} else "ghdl" if language == "vhdl" else ""
    if not tool: return {"status": "skipped", "message": f"Unsupported language: {language}"}
    if not shutil.which(tool): return {"status": "skipped", "message": f"{tool} is not installed"}
    with tempfile.TemporaryDirectory(prefix="codegen2_") as temporary:
        directory = Path(temporary)
        design = directory / f"design{HDL_EXTENSIONS[language]}"
        design.write_text(code, encoding="utf-8")
        if tool == "iverilog": command = [tool, "-g2012", "-tnull", str(design)]
        else: command = [tool, "-a", "--std=08", str(design)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        return {"status": "pass" if result.returncode == 0 else "fail", "tool": tool,
                "message": (result.stdout + result.stderr).strip()[-4000:] or "compiled successfully"}


def cmd_evaluate(args: argparse.Namespace) -> int:
    rows = read_jsonl(Path(args.predictions).resolve())
    results = []
    for position, row in enumerate(rows):
        code = first_text(row, "generated_code", "code", "target_code")
        language = normalized_language(first_text(row, "language"))
        check = compiler_check(code, language) if code else {"status": "fail", "message": "No HDL block found"}
        results.append({"id": first_text(row, "id") or str(position), "language": language, "syntax": check,
                        "approved": check["status"] == "pass", "evaluated_at": now()})
    output = Path(args.output).resolve()
    write_jsonl(output, results)
    passed = sum(result["syntax"]["status"] == "pass" for result in results)
    print(f"Evaluated {len(results)} predictions: {passed} passed, output: {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CodeGen2: open-source multimodal RTL fine-tuning")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Convert approved run records to a fine-tuning dataset")
    prepare.add_argument("--runs", required=True, help="Runs directory, result.json, or approved JSONL")
    prepare.add_argument("--output", required=True, help="Dataset output directory")
    prepare.add_argument("--validation-percent", type=int, default=15, choices=range(0, 100))
    prepare.add_argument("--copy-images", action="store_true", help="Copy source images into the dataset directory")
    train = commands.add_parser("train", help="Fine-tune a Hugging Face vision-language model with LoRA")
    train.add_argument("--dataset", required=True); train.add_argument("--output", default="training")
    train.add_argument("--base-model", default=DEFAULT_MODEL); train.add_argument("--epochs", type=float, default=1.0)
    train.add_argument("--batch-size", type=int, default=1); train.add_argument("--gradient-accumulation", type=int, default=8)
    train.add_argument("--learning-rate", type=float, default=2e-4); train.add_argument("--lora-rank", type=int, default=16)
    train.add_argument("--max-length", type=int, default=2048); train.add_argument("--qlora", action="store_true")
    train.add_argument("--trust-remote-code", action="store_true"); train.add_argument("--dry-run", action="store_true")
    infer = commands.add_parser("infer", help="Generate analysis and RTL using a trained adapter")
    infer.add_argument("--adapter", required=True); infer.add_argument("--image", required=True); infer.add_argument("--instruction", required=True)
    infer.add_argument("--base-model"); infer.add_argument("--output"); infer.add_argument("--max-new-tokens", type=int, default=1024)
    infer.add_argument("--trust-remote-code", action="store_true")
    evaluate = commands.add_parser("evaluate", help="Run HDL syntax checks over prediction JSONL")
    evaluate.add_argument("--predictions", required=True); evaluate.add_argument("--output", default="evaluation.jsonl")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return {"prepare": cmd_prepare, "train": cmd_train, "infer": cmd_infer, "evaluate": cmd_evaluate}[args.command](args)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
