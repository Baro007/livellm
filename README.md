<div align="center">

# ⚡ LiveLLM: Continuous Benchmarking & Nerf Detection Platform
### *An Independent, $0-Cost Community Observatory for Large Language Models*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/downloads/)
[![CI Validation](https://img.shields.io/badge/build-passing-brightgreen.svg)]()
[![Infrastructure Cost](https://img.shields.io/badge/infra%20cost-%240.00%2Fmonth-emerald)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**Canlı Önizleme**](http://localhost:8080) • [**Ölçüm Metodolojisi**](#-ölçüm-metodolojisi) • [**Sıfır Maliyetli Mimari**](#-000-maliyetli-amme-hizmeti-mimarisi) • [**Hızlı Başlangıç**](#-hızlı-başlangıç) • [**Akademik Atıf**](#-akademik-atıf)

---

</div>

## 📌 Neden LiveLLM? (Manifesto & Çıkış Noktası)

> *"Büyük dil modelleri ilk çıktıkları anlardaki performanslarını belli bir süre sonra kaybediyorlar (nerf yiyorlar). Bu durum ticari sağlayıcıların ortak optimizasyon politikasıdır. Aynı zamanda bu modeller gün içinde küresel yoğunluk saatlerinde çok ciddi performans çöküşleri yaşamaktadır."*
> — **Dr. Sadık Barış Adıgüzel**

Bugün yapay zekâ modelleri geleneksel yazılımlar gibi sabit değildir. Servis sağlayıcılar (OpenAI, Anthropic, Google vb.) kullanıcıya haber vermeksizin modelleri:
1. **Maliyet Düşürmek İçin Kuantize Eder:** FP16/BF16 hassasiyetinden INT8/FP8/INT4 seviyelerine indirger; bu da çok adımlı matematiksel ve mantıksal çıkarımlarda mikro aşınmalara yol açar.
2. **Güvenlik Hizalamasıyla Yetenek Kaybettirir (Catastrophic Forgetting):** Sürekli uygulanan RLHF/DPO güvenlik yamaları, güvenlikle ilgisiz olan sembolik akıl yürütme ve kod bloklama kabiliyetlerini bozar.
3. **Dinamik Olarak Yönlendirir (MoE Cascading):** Yoğun saatlerde sorgular amiral gemisi model yerine daha ucuz uzman kümelerine yönlendirilir.
4. **Gün İçi Yoğunlukta (14:00 - 18:00 UTC) Donanım Doygunluğuna Ulaşır:** Bellek (KV önbelleği) dolduğunda istekler baştan hesaplanmaya zorlanır (**drop-and-recompute**), bu da **P99 gecikmesinde 5-10 katlık patlamalara** yol açar.

**LiveLLM**, bu süreci kullanıcı algısından çıkarıp **matematiksel, bağımsız ve 7/24 izlenebilir açık bir kamu gözlemevine** dönüştürmek için tasarlandı.

---

## 🏛️ $0.00 Maliyetli "Amme Hizmeti" Mimarisi

Bir kamu gözlemevinin sürdürülebilir olabilmesi için sunucu ve token faturalarının sıfır olması şarttır. LiveLLM bunu **4 açık kaynak sacayağı** ile başarır:

```mermaid
graph TD
    subgraph "1. Sıfır Token Maliyetli Açık Havuz"
        POL[Pollinations.ai • 100% Açık Gateway]
        ORF[OpenRouter :free Model Havuzu]
        GAS[Google AI Studio • 15 RPM Ücretsiz]
        GROQ[Groq Cloud • 30 RPM Ücretsiz]
        GHM[GitHub Models • Azure AI PAT]
    end

    subgraph "2. Sıfır Sunucu Maliyetli Otomasyon ($0/ay)"
        GHA[GitHub Actions Cron • Her 10 dk]
        CRON[cron_probe.py • SymPy & Sandbox]
    end

    subgraph "3. Dağıtık Topluluk Gözlemcisi (Citizen Telemetry)"
        USERS[Web Ziyaretçileri / Dağıtık Düğümler]
        PULSE[Tarayıcı İçi Hafif Mikro-Puls]
    end

    subgraph "4. Açık Kamu Veri Tabanı"
        DB[(Açık SQLite / JSON)]
        EXP[/api/export/dataset • CC-BY-4.0]
        WEB[LiveLLM Web Dashboard]
    end

    POL & ORF & GAS & GROQ & GHM --> CRON
    GHA --> CRON
    CRON --> DB
    USERS --> PULSE --> DB
    DB --> WEB & EXP
```

1. **Açık Ağ Geçitleri:** Pollinations.ai (anahtarsız doğrudan çıkarım), OpenRouter `:free` havuzu, Google AI Studio (15 RPM ücretsiz), Groq (30 RPM ücretsiz) ve GitHub Models ile $0 token maliyeti.
2. **GitHub Actions Ücretsiz Cron:** [`.github/workflows/continuous_benchmark.yml`](.github/workflows/continuous_benchmark.yml) iş akışı her 10 dakikada bir GitHub ücretsiz sunucularında uyanır, modelleri test eder ve sonuçları depoya kaydeder.
3. **Dağıtık Topluluk Gözlemcisi (Citizen Telemetry):** Ziyaretçilerin tarayıcıları arka planda opt-in olarak ücretsiz testlere katılır; Türkiye ve dünya genelindeki gerçek kullanıcı ISS gecikmeleri toplanır.
4. **Açık Araştırma Veri Seti:** `/api/export/dataset` üzerinden tüm gözlem verileri kamuya açıktır.

---

## 🔬 Ölçüm Metodolojisi

1. **Önbellek Kırma (Cache Busting):** Sağlayıcıların "Prompt Caching" hilesini kırmak için her isteme dinamik `[Nonce: UUID4]` eklenir.
2. **Evrensel Tokenizer Normalizasyonu:** Farklı sözlük boyutlarının hız kıyasını yanıltmasını engellemek için tüm çıktılar `tiktoken` (`o200k_base`) ile sayılarak normalize **TPS** hesaplanır.
3. **Deterministik Zemin Gerçek (Zero LLM-as-a-judge Bias):**
   - **Matematik:** `\boxed{...}` içindeki yanıt **SymPy** ile sembolik eşitlik testine tabi tutulur ($1/2 \equiv 0.5 \equiv \frac{2}{4}$).
   - **Kodlama:** Python kodları izole sandbox'ta gizli birim testlerle (**pass@1**) koşturulur.
4. **Page-Hinkley İstatistiksel Nerf Tespiti:**
   $$m_t = \sum_{i=1}^t (e_i - \bar{x}_i + \delta), \quad M_t = \min_{1 \le i \le t} m_i, \quad PH_t = m_t - M_t$$
   $PH_t > \lambda$ olduğunda doğrulanmış **"Model Nerf Alert"** üretilir.

---

## 🚀 Hızlı Başlangıç

### Seçenek 1: Yerel Olarak Çalıştırma
```bash
git clone https://github.com/Baro007/livellm.git
cd livellm

# Başlatma betiği (sanal ortamı otomatik kurar ve sunucuyu açar)
./run.sh
```
Tarayıcınızda açın: **`http://localhost:8080`**

### Seçenek 2: Netlify Üzerinde Sıfır Maliyetli Canlı Yayın (Jamstack)
LiveLLM, GitHub Actions cron'unun her 10 dakikada bir ürettiği statik JSON veri seti sayesinde **Netlify üzerinde $0.00 maliyetle 7/24 kesintisiz** yayınlanır.

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/Baro007/livellm)

1. [Netlify](https://app.netlify.com) üzerinde **"Add new site" -> "Import an existing project"** diyerek **`Baro007/livellm`** deponuzu seçin.
2. [`netlify.toml`](netlify.toml) yapılandırması sayesinde tüm ayarlar (yayın dizini: `livellm/frontend`, yönlendirmeler ve güvenlik başlıkları) otomatik uygulanır.
3. **"Deploy LiveLLM"** butonuna tıklayın. GitHub Actions her 10 dakikada bir veri setini güncellediğinde, Netlify sitenizi otomatik olarak canlıya alır.

### Seçenek 3: Docker ile Çalıştırma
```bash
docker compose up -d
```

### Testleri Koşturma
```bash
pytest -v tests/
```

---

## 📁 Proje Mimarisi

```
livellm/
├── .github/
│   ├── workflows/
│   │   ├── continuous_benchmark.yml   # 30 dakikada bir çalışan $0 cron otomasyonu
│   │   └── ci.yml                     # Otomatik test iş akışı
│   └── ISSUE_TEMPLATE/
│       ├── nerf_incident_report.md    # Topluluk nerf bildirim şablonu
│       └── model_request.md           # Yeni model istek şablonu
├── livellm/
│   ├── core/                          # Telemetri, cache buster, dinamik katalog
│   │   ├── telemetry.py
│   │   ├── cache_buster.py
│   │   ├── dynamic_catalog.py         # Canlı OpenRouter / Astra katalog keşfi
│   │   ├── open_providers.py          # Sıfır maliyetli açık ağ geçitleri
│   │   └── provider_client.py         # Canlı SSE akış istemcisi
│   ├── evaluators/                    # SymPy, Code Sandbox & JSON doğrulayıcılar
│   ├── statistical/                   # Page-Hinkley & CUSUM nerf algoritmaları
│   ├── storage/                       # SQLite veritabanı & tohumlayıcı
│   ├── api/                           # FastAPI REST uç noktaları & export
│   └── frontend/                      # Modern obsidian karanlık web arayüzü
├── tests/                             # 15+ otomatik birim ve entegrasyon testi
├── Dockerfile & docker-compose.yml
├── run.sh
└── LICENSE (MIT)
```

---

## 📜 Akademik Atıf

Bu projeyi akademik araştırmalarınızda veya yayınlarınızda kullanırsanız lütfen şu şekilde atıfta bulunun:

```bibtex
@software{adiguzel2026livellm,
  author = {Dr. Sadık Barış Adıgüzel},
  title = {LiveLLM: Continuous Benchmarking, Quantization Drift, and Nerf Detection Platform for Large Language Models},
  year = {2026},
  url = {https://github.com/Baro007/livellm}
}
```

---

<div align="center">
  <b>Dr. Sadık Barış Adıgüzel</b> • Antalya Eğitim ve Araştırma Hastanesi<br>
  <i>Tıbbi Yapay Zekâ, Klinik Karar Destek Sistemleri ve Bağımsız Model Gözlemlenebilirliği</i>
</div>
