"""Interpolación de fotogramas con RIFE 4.9 en CPU (Apache-2.0, pesos de la comunidad).

Usa la arquitectura del nodo ComfyUI-Frame-Interpolation y los pesos rife49.pth.
    from rife_cpu import Rife
    r = Rife()
    mid = r.between(img0_bgr, img1_bgr, t=0.5)   # arrays uint8 HxWx3
"""
import sys
from pathlib import Path
import numpy as np, torch, torch.nn.functional as F

NODE = Path.home() / "ComfyUI" / "custom_nodes" / "ComfyUI-Frame-Interpolation"
import types                                              # rife_arch importa comfy.model_management solo para
_mm = types.ModuleType("comfy.model_management")          # elegir dispositivo: aquí siempre es la CPU
_mm.get_torch_device = lambda: torch.device("cpu")
_pkg = types.ModuleType("comfy"); _pkg.model_management = _mm
sys.modules.setdefault("comfy", _pkg); sys.modules["comfy.model_management"] = _mm
sys.path.insert(0, str(NODE / "vfi_models" / "rife"))
from rife_arch import IFNet  # noqa: E402

torch.set_num_threads(max(1, torch.get_num_threads()))


class Rife:
    def __init__(self, ckpt=NODE / "ckpts" / "rife" / "rife49.pth", scale=1.0):
        self.model = IFNet(arch_ver="4.7")
        self.model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=False))
        self.model.eval()
        self.scale_list = [8 / scale, 4 / scale, 2 / scale, 1 / scale]

    @staticmethod
    def _to_tensor(img):
        t = torch.from_numpy(np.ascontiguousarray(img[:, :, ::-1])).permute(2, 0, 1).float().div_(255).unsqueeze(0)
        return t

    @torch.no_grad()
    def between(self, img0, img1, t=0.5, ensemble=False):
        a, b = self._to_tensor(img0), self._to_tensor(img1)
        h, w = a.shape[2:]
        ph, pw = (-h) % 64, (-w) % 64
        if ph or pw:
            a = F.pad(a, (0, pw, 0, ph), mode="replicate")
            b = F.pad(b, (0, pw, 0, ph), mode="replicate")
        out = self.model(a, b, timestep=float(t), scale_list=self.scale_list,
                         training=False, fastmode=True, ensemble=ensemble)
        out = out[:, :, :h, :w].clamp_(0, 1).mul_(255).round_().byte()[0].permute(1, 2, 0).numpy()
        return np.ascontiguousarray(out[:, :, ::-1])


if __name__ == "__main__":  # prueba rápida: python rife_cpu.py a.png b.png salida.png
    import cv2, time
    r = Rife()
    i0, i1 = cv2.imread(sys.argv[1]), cv2.imread(sys.argv[2])
    t0 = time.time(); m = r.between(i0, i1, 0.5); dt = time.time() - t0
    cv2.imwrite(sys.argv[3], m)
    print(f"{i0.shape[1]}x{i0.shape[0]} en {dt:.2f} s")
