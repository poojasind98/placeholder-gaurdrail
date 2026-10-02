"""Check the actual 4-bit inference backend before downloading base models."""
import torch
import bitsandbytes as bnb


def main():
    print(f"PyTorch: {torch.__version__}; bitsandbytes: {bnb.__version__}", flush=True)
    if not torch.backends.mps.is_available():
        raise SystemExit("Apple GPU (MPS) is unavailable in this Python process.")
    layer = bnb.nn.Linear4bit(
        64, 64, bias=False, compute_dtype=torch.float16,
        quant_type="nf4", compress_statistics=False,
    )
    with torch.no_grad():
        layer.weight.normal_(0, 0.02)
        layer = layer.to("mps")
        result = layer(torch.randn(1, 64, device="mps", dtype=torch.float16))
    if not torch.isfinite(result).all().item():
        raise SystemExit("4-bit operation returned non-finite values.")
    print("PASS: 4-bit inference works on the Mac GPU.")


if __name__ == "__main__":
    main()
