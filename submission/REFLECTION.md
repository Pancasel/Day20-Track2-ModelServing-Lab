# Reflection — Lab 20 (Personal Report)

> **Đây là báo cáo cá nhân.** Mỗi học viên chạy lab trên laptop của mình, với spec của mình. Số liệu của bạn không so sánh được với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính theo độ rõ ràng của setup + tuning của bạn, không phải tốc độ tuyệt đối.

---

**Họ Tên:** Đỗ Quốc An
**Cohort:** 2A202600952
**Ngày submit:** 2026-06-24

---

## 1. Hardware spec (từ `00-setup/detect-hardware.py`)

- **OS:** Windows 11 (AMD64)
- **CPU:** 12th Gen Intel(R) Core(TM) i5-12450H
- **Cores:** 8 physical · 12 logical cores
- **CPU extensions:** AVX2
- **RAM:** 15.7 GB
- **Accelerator:** NVIDIA GeForce RTX 4050 Laptop GPU (6GB VRAM)
- **llama.cpp backend đã chọn:** CUDA (GGML_CUDA=on)
- **Recommended model tier:** Qwen2.5-1.5B

**Setup story** (≤ 80 chữ): những gì cần thay đổi để lab chạy được trên máy bạn (vd: dùng WSL2, install CUDA Toolkit, fall back sang Vulkan vì ROCm phiên bản kén, tắt antivirus để pip install nhanh hơn, v.v.):

Để lab chạy được trên Windows, em sử dụng PowerShell kích hoạt môi trường ảo, thay đổi cổng mặc định sang 8089 do cổng 8080 bị MTAgentService chiếm dụng. Đồng thời, cấu hình thư mục TMP ngắn (D:\t) để vượt qua lỗi giới hạn độ dài ký tự đường dẫn file khi cài đặt llama-cpp-python và biên dịch thành công llama-server qua CMake.

---

## 2. Track 01 — Quickstart numbers (từ `benchmarks/01-quickstart-results.md`)

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| qwen2.5-1.5b-instruct-q4_k_m.gguf (Q4_K_M) | 1240 | 125.6 / 158.0 | 31.1 / 32.0 | 1888.8 / 2104.3 / 2205.0 | 35.9 |
| qwen2.5-1.5b-instruct-q2_k.gguf (Q2_K)   | 652 | 123.0 / 188.0 | 22.8 / 32.7 | 1559.0 / 2322.0 / 2370.0 | 34.7 |

**Một quan sát** (≤ 50 chữ): Q4_K_M vs Q2_K trên máy bạn — số liệu nói gì? Quality đáng đánh đổi không?

Bản Q4_K_M cho chất lượng câu trả lời tốt vượt trội và dung lượng RAM chênh lệch không đáng kể so với Q2_K trên máy của em. Thời gian nạp (load) của Q4_K_M chậm hơn gấp đôi nhưng tốc độ sinh (TPOT) gần như tương đương, rất đáng để đánh đổi.

---

## 3. Track 02 — llama-server load test

| Concurrency | Total RPS | TTFB P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 0.72 | 10000 | 18000 | 20000 | 0 |
| 50 | 0.83 | 17000 | 29000 | 30000 | 0 |

**Batching observation** (từ `record-metrics.py`): peak `llamacpp:n_busy_slots_per_decode` / `requests_processing` ở concurrency 50 = `3.71 / 4`, nghĩa là máy đang chạy batching cực kỳ bận rộn gần đạt giới hạn tối đa 4 parallel slots. Hàng đợi của server lúc tải đỉnh ghi nhận 6 requests bị trì hoãn (deferred), chứng tỏ cơ chế xếp hàng đợi hoạt động hoàn hảo.

---

## 4. Track 03 — Milestone integration

- **N16 (Cloud/IaC):** stub: localhost only
- **N17 (Data pipeline):** stub: in-memory dict
- **N18 (Lakehouse):** stub: SQLite
- **N19 (Vector + Feature Store):** stub: TOY_DOCS

**Nơi tốn nhiều ms nhất** trong pipeline (đo bằng `time.perf_counter` trong `pipeline.py`):

- embed: 0.0 ms
- retrieve: 0.0 ms
- llama-server: 6284.6 ms

**Reflection** (≤ 60 chữ): bottleneck nằm ở đâu? Có khớp với kỳ vọng không?

Đúng như dự đoán, llama-server chiếm hơn 99.9% độ trễ của toàn bộ pipeline do các phép tính toán ma trận của mạng nơ-ron sinh token có độ phức tạp thuật toán cực kỳ cao so với các tác vụ tìm kiếm từ khóa cục bộ.

---

## 5. Bonus — The single change that mattered most

> **Most important section.** Pick **một** thay đổi từ bonus track (build flag, thread sweep, quant pick, GPU offload, KV-cache quantization, speculative decoding, bất cứ challenge nào trong `BONUS-llama-cpp-optimization/CHALLENGES.md`) đã tạo ra speedup lớn nhất trên máy bạn.

**Change:** Thread sweep using llama-bench

**Before vs after** (paste 2-3 dòng từ sweep output):

```text
before: 5.5 tok/s (at -t 1)
after:  37.6 tok/s (at -t 8 - Best)
speedup: ~6.8x
```

**Tại sao nó work** (1—2 đoạn ngắn — đây là phần grader đọc kỹ nhất):

Vi xử lý 12th Gen Intel Core i5-12450H của máy em có 8 nhân vật lý (physical cores). Do tác vụ giải mã (decode) của LLM bị giới hạn bởi băng thông bộ nhớ (memory-bandwidth-bound), việc phân bổ số luồng tối ưu trùng khớp với số nhân vật lý (8 threads) cho hiệu năng tốt nhất (37.6 tok/s), cải thiện gấp 6.8 lần so với chạy đơn luồng.

Khi nâng số luồng lên 12 hoặc 24 (oversubscribe), các nhân ảo bắt đầu tranh chấp tài nguyên bộ nhớ đệm cache và bus RAM, dẫn đến việc xung đột tài nguyên và làm giảm tốc độ sinh token xuống còn 32.4 tok/s và 28.0 tok/s.

---

## 6. (Optional) Điều ngạc nhiên nhất

Mặc dù máy em chạy CPU do llama.cpp biên dịch thuần, nhưng nhờ việc offload toàn bộ 99 layers sang GPU RTX 4050 bằng backend CUDA, tốc độ sinh token vẫn cực kỳ mượt mà và không hề bị giật lag.

---

## 7. Self-graded checklist

- [x] `hardware.json` đã commit
- [x] `models/active.json` đã commit (hoặc paste path snapshot vào section 1)
- [x] `benchmarks/01-quickstart-results.md` đã commit
- [x] `benchmarks/02-server-results.md` (hoặc CSV từ `record-metrics.py`) đã commit
- [x] `benchmarks/bonus-*.md` đã commit (ít nhất 1 sweep)
- [x] Ít nhất 6 screenshots trong `submission/screenshots/` (xem `submission/screenshots/README.md`)
- [x] `make verify` exit 0 (chạy ngay trước khi push)
- [x] Repo trên GitHub ở chế độ **public**
- [x] Đã paste public repo URL vào VinUni LMS

---

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.
