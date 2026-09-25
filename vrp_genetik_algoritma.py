"""
Genetik Algoritma ile Kapasiteli Araç Rotalama Problemi (CVRP)
=================================================================

Endüstri Mühendisliği - Lojistik & Dağıtım Optimizasyonu

Problem (CVRP - Capacitated Vehicle Routing Problem):
    Bir depodan, talepleri bilinen n müşteriye, kapasitesi sabit
    araçlarla dağıtım yapılacaktır. Her müşteri tam olarak bir araç
    tarafından, tam olarak bir kez ziyaret edilmelidir. Her aracın
    rotası depodan başlar ve depoda biter. Bir aracın taşıdığı toplam
    talep, araç kapasitesini (Q) aşamaz.

    Amaç: Tüm araçların toplam kat ettiği mesafeyi minimize etmek.

    Bu problem NP-hard'dır; n büyüdükçe kesin (optimal) çözüm makul
    zamanda bulunamaz. Bu yüzden GENETİK ALGORİTMA gibi sezgisel/
    metasezgisel yöntemler kullanılır.

Kodlama (Chromosome Encoding):
    Bir kromozom, müşterilerin bir permütasyonudur (ziyaret sırası).
    Bu "dev tur" (giant tour), kapasite sınırını aşmadan art arda
    araçlara bölünerek gerçek rotalara dönüştürülür (route splitting).

Genetik Operatörler:
    - Seçilim   : Turnuva seçilimi (tournament selection)
    - Çaprazlama: Sıralı çaprazlama (Order Crossover - OX1)
    - Mutasyon  : İki geni yer değiştirme (swap mutation)
    - Elitizm   : En iyi bireyler doğrudan bir sonraki nesle taşınır

Kullanım:
    python vrp_genetik_algoritma.py
"""

from dataclasses import dataclass
import math
import random


# --------------------------------------------------------------------------
# Problem Tanımı
# --------------------------------------------------------------------------

@dataclass
class Musteri:
    id: int
    x: float
    y: float
    talep: float


@dataclass
class VRPProblemi:
    depo: tuple[float, float]
    musteriler: list[Musteri]
    arac_kapasitesi: float

    def mesafe(self, p1: tuple[float, float], p2: tuple[float, float]) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def koordinat(self, musteri_id: int) -> tuple[float, float]:
        if musteri_id == 0:
            return self.depo
        return next((m.x, m.y) for m in self.musteriler if m.id == musteri_id)


def rastgele_problem_uret(n_musteri=25, arac_kapasitesi=100, seed=7) -> VRPProblemi:
    """Test amaçlı rastgele bir CVRP örneği üretir."""
    rnd = random.Random(seed)
    depo = (50.0, 50.0)
    musteriler = [
        Musteri(
            id=i + 1,
            x=rnd.uniform(0, 100),
            y=rnd.uniform(0, 100),
            talep=rnd.randint(5, 25),
        )
        for i in range(n_musteri)
    ]
    return VRPProblemi(depo=depo, musteriler=musteriler, arac_kapasitesi=arac_kapasitesi)


# --------------------------------------------------------------------------
# Kromozom Çözümleme: Dev Tur -> Gerçek Rotalar
# --------------------------------------------------------------------------

def rotalara_ayir(problem: VRPProblemi, kromozom: list[int]) -> list[list[int]]:
    """
    Bir permütasyonu (dev tur), kapasite sınırını aşmadan
    ayrı araç rotalarına böler (greedy split).
    """
    musteri_dict = {m.id: m for m in problem.musteriler}
    rotalar = []
    guncel_rota = []
    guncel_yuk = 0.0

    for musteri_id in kromozom:
        talep = musteri_dict[musteri_id].talep
        if guncel_yuk + talep > problem.arac_kapasitesi:
            rotalar.append(guncel_rota)
            guncel_rota = [musteri_id]
            guncel_yuk = talep
        else:
            guncel_rota.append(musteri_id)
            guncel_yuk += talep

    if guncel_rota:
        rotalar.append(guncel_rota)

    return rotalar


def toplam_mesafe(problem: VRPProblemi, rotalar: list[list[int]]) -> float:
    """Depo -> müşteriler -> depo şeklindeki tüm rotaların toplam mesafesi."""
    toplam = 0.0
    for rota in rotalar:
        nokta_onceki = problem.depo
        for musteri_id in rota:
            nokta = problem.koordinat(musteri_id)
            toplam += problem.mesafe(nokta_onceki, nokta)
            nokta_onceki = nokta
        toplam += problem.mesafe(nokta_onceki, problem.depo)  # depoya dönüş
    return toplam


def fitness(problem: VRPProblemi, kromozom: list[int]) -> float:
    """Fitness = 1 / toplam_mesafe olarak DEĞİL, doğrudan mesafeyi
    minimize edeceğimiz için burada sadece mesafeyi döndürüyoruz."""
    rotalar = rotalara_ayir(problem, kromozom)
    return toplam_mesafe(problem, rotalar)


# --------------------------------------------------------------------------
# Genetik Algoritma Operatörleri
# --------------------------------------------------------------------------

def baslangic_populasyonu(problem: VRPProblemi, boyut: int, rnd: random.Random) -> list[list[int]]:
    temel = [m.id for m in problem.musteriler]
    populasyon = []
    for _ in range(boyut):
        birey = temel.copy()
        rnd.shuffle(birey)
        populasyon.append(birey)
    return populasyon


def turnuva_secimi(populasyon: list[list[int]], skorlar: list[float],
                    k: int, rnd: random.Random) -> list[int]:
    """k bireylik turnuvadan en iyi (en düşük mesafeli) bireyi seçer."""
    secilenler = rnd.sample(range(len(populasyon)), k)
    en_iyi_idx = min(secilenler, key=lambda i: skorlar[i])
    return populasyon[en_iyi_idx]


def siralamali_caprazlama(ebeveyn1: list[int], ebeveyn2: list[int],
                            rnd: random.Random) -> list[int]:
    """Order Crossover (OX1): ebeveyn1'den bir alt-dizi korunur,
    kalan genler ebeveyn2'nin sırasına göre doldurulur."""
    n = len(ebeveyn1)
    kesim1, kesim2 = sorted(rnd.sample(range(n), 2))

    cocuk = [None] * n
    cocuk[kesim1:kesim2] = ebeveyn1[kesim1:kesim2]

    dolu_genler = set(cocuk[kesim1:kesim2])
    ebeveyn2_kalan = [g for g in ebeveyn2 if g not in dolu_genler]

    idx = 0
    for i in range(n):
        if cocuk[i] is None:
            cocuk[i] = ebeveyn2_kalan[idx]
            idx += 1

    return cocuk


def swap_mutasyonu(birey: list[int], oran: float, rnd: random.Random) -> list[int]:
    birey = birey.copy()
    if rnd.random() < oran:
        i, j = rnd.sample(range(len(birey)), 2)
        birey[i], birey[j] = birey[j], birey[i]
    return birey


# --------------------------------------------------------------------------
# Genetik Algoritma - Ana Döngü
# --------------------------------------------------------------------------

def genetik_algoritma_calistir(
    problem: VRPProblemi,
    populasyon_boyutu: int = 150,
    nesil_sayisi: int = 300,
    turnuva_k: int = 5,
    mutasyon_orani: float = 0.15,
    elit_sayisi: int = 5,
    seed: int = 42,
):
    rnd = random.Random(seed)
    populasyon = baslangic_populasyonu(problem, populasyon_boyutu, rnd)
    en_iyi_gecmis = []  # her nesildeki en iyi mesafe (yakınsama grafiği için)

    en_iyi_kromozom = None
    en_iyi_skor = math.inf

    for nesil in range(nesil_sayisi):
        skorlar = [fitness(problem, birey) for birey in populasyon]

        nesil_en_iyi_idx = min(range(len(populasyon)), key=lambda i: skorlar[i])
        if skorlar[nesil_en_iyi_idx] < en_iyi_skor:
            en_iyi_skor = skorlar[nesil_en_iyi_idx]
            en_iyi_kromozom = populasyon[nesil_en_iyi_idx].copy()

        en_iyi_gecmis.append(en_iyi_skor)

        # Elitizm: en iyi bireyleri doğrudan yeni nesle taşı
        elitler_idx = sorted(range(len(populasyon)), key=lambda i: skorlar[i])[:elit_sayisi]
        yeni_populasyon = [populasyon[i].copy() for i in elitler_idx]

        # Kalan bireyleri çaprazlama + mutasyon ile üret
        while len(yeni_populasyon) < populasyon_boyutu:
            ebeveyn1 = turnuva_secimi(populasyon, skorlar, turnuva_k, rnd)
            ebeveyn2 = turnuva_secimi(populasyon, skorlar, turnuva_k, rnd)
            cocuk = siralamali_caprazlama(ebeveyn1, ebeveyn2, rnd)
            cocuk = swap_mutasyonu(cocuk, mutasyon_orani, rnd)
            yeni_populasyon.append(cocuk)

        populasyon = yeni_populasyon

    return en_iyi_kromozom, en_iyi_skor, en_iyi_gecmis


if __name__ == "__main__":
    problem = rastgele_problem_uret(n_musteri=25, arac_kapasitesi=100)

    print(f"Müşteri sayısı: {len(problem.musteriler)}")
    print(f"Araç kapasitesi: {problem.arac_kapasitesi}")
    print(f"Toplam talep: {sum(m.talep for m in problem.musteriler)}")

    # Karşılaştırma amaçlı: tamamen rastgele bir çözüm
    rnd_baseline = random.Random(1)
    rastgele_kromozom = [m.id for m in problem.musteriler]
    rnd_baseline.shuffle(rastgele_kromozom)
    rastgele_rotalar = rotalara_ayir(problem, rastgele_kromozom)
    rastgele_mesafe = toplam_mesafe(problem, rastgele_rotalar)

    print(f"\nRastgele çözüm  -> Araç sayısı: {len(rastgele_rotalar)}  "
          f"Toplam mesafe: {rastgele_mesafe:.1f}")

    # Genetik algoritma ile optimizasyon
    en_iyi_kromozom, en_iyi_skor, gecmis = genetik_algoritma_calistir(problem)
    en_iyi_rotalar = rotalara_ayir(problem, en_iyi_kromozom)

    print(f"\nGA Çözümü       -> Araç sayısı: {len(en_iyi_rotalar)}  "
          f"Toplam mesafe: {en_iyi_skor:.1f}")

    for i, rota in enumerate(en_iyi_rotalar, 1):
        yuk = sum(m.talep for m in problem.musteriler if m.id in rota)
        print(f"  Araç {i}: Depo -> {' -> '.join(map(str, rota))} -> Depo   "
              f"(Yük: {yuk}/{problem.arac_kapasitesi})")

    iyilesme = (rastgele_mesafe - en_iyi_skor) / rastgele_mesafe * 100
    print(f"\nRastgele çözüme göre iyileşme: %{iyilesme:.1f}")
