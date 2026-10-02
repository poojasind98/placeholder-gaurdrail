"""Offline integration check using tiny random models, not benchmark results.

Exercises 4-bit loading, BERT/projector/Llama inference, and adapter reloads.
Run from the project root: python tests/check_model_backend.py
"""
import sys
import tempfile
from pathlib import Path

import torch
from tokenizers import Tokenizer, models, pre_tokenizers, processors
from transformers import (BertConfig, BertModel, BertTokenizerFast,
                          LlamaConfig, LlamaForCausalLM, PreTrainedTokenizerFast)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import LogLLM
from customDataset import CustomCollator


def main():
    if not torch.backends.mps.is_available():
        raise SystemExit("Run outside the sandbox to access MPS.")
    torch.manual_seed(42)
    with tempfile.TemporaryDirectory(prefix="logllm-backend-") as temp:
        root = Path(temp)
        bert, llama, adapters = root / "bert", root / "llama", root / "adapters"
        bert.mkdir()
        llama.mkdir()
        vocab = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]", "normal", "anomalous",
                 "the", "sequence", "is", "error", "service", "started", "stopped", ".", "log"]
        (bert / "vocab.txt").write_text("\n".join(vocab) + "\n")
        BertTokenizerFast(vocab_file=str(bert / "vocab.txt")).save_pretrained(bert)
        BertModel(BertConfig(vocab_size=len(vocab), hidden_size=64, num_hidden_layers=1,
                             num_attention_heads=4, intermediate_size=128)).save_pretrained(bert)
        tokenizer = Tokenizer(models.WordLevel({word: i for i, word in enumerate(vocab)}, unk_token="[UNK]"))
        tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
        tokenizer.post_processor = processors.TemplateProcessing(
            single="[CLS] $A", special_tokens=[("[CLS]", 2)])
        PreTrainedTokenizerFast(tokenizer_object=tokenizer, bos_token="[CLS]",
                                eos_token="[SEP]", pad_token="[PAD]", unk_token="[UNK]").save_pretrained(llama)
        LlamaForCausalLM(LlamaConfig(vocab_size=len(vocab), hidden_size=64,
                                     intermediate_size=128, num_hidden_layers=1,
                                     num_attention_heads=4, num_key_value_heads=2,
                                     bos_token_id=2, eos_token_id=3, pad_token_id=0)).save_pretrained(llama)
        model = LogLLM(str(bert), str(llama), is_train_mode=False, device=torch.device("mps"))
        collator = CustomCollator(model.Bert_tokenizer)
        batch = collator([(["service started", "service stopped"], 0), (["error"], 1)])
        model.eval()
        with torch.inference_mode():
            predicted = model(batch["inputs"].to("mps"), batch["seq_positions"])
        assert predicted.shape[0] == 2 and 1 <= predicted.shape[1] <= 6
        model.save_ft_model(str(adapters))
        del model
        torch.mps.empty_cache()
        restored = LogLLM(str(bert), str(llama), ft_path=str(adapters),
                           is_train_mode=False, device=torch.device("mps"))
        restored.eval()
        with torch.inference_mode():
            repeated = restored(batch["inputs"].to("mps"), batch["seq_positions"])
        assert torch.equal(predicted, repeated), "Adapter reload changed generated tokens"
        print("PASS: tiny quantized BERT -> projector -> Llama inference and adapter reload on MPS.")
        print("This is a compatibility check with random weights, not trained-model validation.")


if __name__ == "__main__":
    main()
