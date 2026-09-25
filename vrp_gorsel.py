"""
VRP Görselleştirme
====================
Genetik algoritma ile bulunan rotaları harita üzerinde renkli
çizer ve nesiller boyunca yakınsama (convergence) grafiğini üretir.
"""

import random
import matplotlib.pyplot as plt

from vrp_genetik_algoritma import (
    rastgele_problem_uret,
    rotalara_ayir,
    toplam_mesafe,
    genetik_algoritma_calistir,
)


def rotalari_ciz(ax, problem, rotalar, baslik):
    renkler = plt.cm.tab10.colors

    # Depo
    ax.scatter(*problem.depo, c="black", marker="s", s=160, zorder=5, label="Depo")

    for i, rota in enumerate(rotalar):
        renk = renkler[i % len(renkler)]
        noktalar = [problem.depo] + [problem.koordinat(m) for m in rota] + [problem.depo]
        xs, ys = zip(*noktalar)
        ax.plot(xs, ys, "-o", color=renk, linewidth=1.8, markersize=6,
                 label=f"Araç {i + 1} (yük: {sum(m2.talep for m2 in problem.musteriler if m2.id in rota)})")

    for m in problem.musteriler:
        ax.annotate(str(m.id), (m.x, m.y), fontsize=7, ha="center", va="bottom")

    ax.set_title(baslik)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")


def main():
    problem = rastgele_problem_uret(n_musteri=25, arac_kapasitesi=100)

    # Karşılaştırma: rastgele çözüm
    rnd_baseline = random.Random(1)
    rastgele_kromozom = [m.id for m in problem.musteriler]
    rnd_baseline.shuffle(rastgele_kromozom)
    rastgele_rotalar = rotalara_ayir(problem, rastgele_kromozom)
    rastgele_mesafe = toplam_mesafe(problem, rastgele_rotalar)

    # GA çözümü
    en_iyi_kromozom, en_iyi_skor, gecmis = genetik_algoritma_calistir(problem)
    en_iyi_rotalar = rotalara_ayir(problem, en_iyi_kromozom)

    # --- Görsel 1: Rota karşılaştırması ---
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    rotalari_ciz(ax1, problem, rastgele_rotalar,
                 f"Rastgele Çözüm (Mesafe = {rastgele_mesafe:.0f})")
    rotalari_ciz(ax2, problem, en_iyi_rotalar,
                 f"Genetik Algoritma Çözümü (Mesafe = {en_iyi_skor:.0f})")

    iyilesme = (rastgele_mesafe - en_iyi_skor) / rastgele_mesafe * 100
    fig1.suptitle(f"VRP - Genetik Algoritma Karşılaştırması (İyileşme: %{iyilesme:.1f})",
                  fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig("vrp_rota_karsilastirma.png", dpi=150)
    plt.close(fig1)

    # --- Görsel 2: Yakınsama grafiği ---
    fig2, ax = plt.subplots(figsize=(9, 5))
    ax.plot(gecmis, color="#2E86AB", linewidth=2)
    ax.set_title("Genetik Algoritma Yakınsama Grafiği")
    ax.set_xlabel("Nesil")
    ax.set_ylabel("En İyi Toplam Mesafe")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("vrp_yakinsama.png", dpi=150)
    plt.close(fig2)

    print("Görseller kaydedildi: vrp_rota_karsilastirma.png, vrp_yakinsama.png")
    print(f"Rastgele: {rastgele_mesafe:.1f}  |  GA: {en_iyi_skor:.1f}  |  İyileşme: %{iyilesme:.1f}")


if __name__ == "__main__":
    main()
