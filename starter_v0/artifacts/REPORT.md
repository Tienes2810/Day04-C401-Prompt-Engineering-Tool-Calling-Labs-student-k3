# Day 04 Lab v2 Report — Research Agent

## Team

- Team: Group AI20K - Day 04 Research Agent
- Members:
  - Lê Hoàng Việt (MSSV: 2A202601543) - Leader / Prompt & Eval
  - Trần Tiến Dũng (MSSV: 2A202601783) - Tool Developer
  - Nguyễn Thiên Tài (MSSV: 2A202601849) - UI & Integration
  - Nguyễn Tiến (MSSV: 2A202601655) - Reporter & Testing
- Provider/model: Gemini / `gemini-3.5-flash-lite`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

AI Research Agent thông minh giúp tự động hóa quá trình nghiên cứu công nghệ: tìm kiếm kho lưu trữ mã nguồn mở GitHub (`repo_search`), tra cứu tin tức thời sự công nghệ (`lookup`), tổng hợp các bài đăng Twitter/X (`timeline`, `social_search`), đọc nội dung bài viết từ liên kết (`fetch`), tự động hỏi lại người dùng khi thiếu thông tin (`clarify`), và xin xác nhận an toàn trước khi thực hiện hành động xuất bản (`send`).

**Link dùng thử (truy cập được trong showdown):**

- Localhost Demo URL: `http://localhost:8501`

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc xin xác nhận trước khi thực hiện hành động | Không |
| timeline | Lấy danh sách các bài đăng (tweets) gần đây từ một tài khoản cụ thể | Không |
| social_search | Tìm kiếm bài đăng theo chủ đề / từ khóa trên Twitter (sắp xếp Top / Latest) | Không |
| lookup | Tra cứu thông tin tin tức web thời sự theo khoảng thời gian (day/week/month) | Không |
| fetch | Lấy và đọc nội dung văn bản đầy đủ từ một địa chỉ URL | Không |
| format | Định dạng danh sách thông tin đã thu thập thành bản tin / digest | Không |
| send | Gửi bài đăng / tin nhắn thông tin lên các kênh truyền thông (Telegram) | Không |
| repo_search | Tìm kiếm kho lưu trữ mã nguồn mở trên GitHub theo ngôn ngữ và tiêu chí sắp xếp | **Có (Custom Tool)** |

## A3. Câu hỏi mẫu để thử

1. `Tìm các repo GitHub Python phổ biến nhất về LLM Agent`
2. `Tin tức AI hôm nay có gì nổi bật?`
3. `Tóm tắt 5 tweet mới nhất` (Agent sẽ chủ động hỏi lại tên tài khoản)
4. `Đăng bài viết từ link https://openai.com/blog/gpt-5 lên channel Telegram giúp mình` (Agent sẽ xin xác nhận trước khi gửi)

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| 1. Tìm kiếm dự án mã nguồn mở | `repo_search(query="LLM Agent", language="python", sort="stars")` | **Tool mới**: Nhóm tự thiết kế tool `repo_search` tích hợp trực tiếp GitHub API | `runs/v3_B_group_gemini_20260729T101435533000.json` |
| 2. Hỏi lại khi thiếu thông tin | `clarify(question="...", response_type="text")` | **v0 ➔ v1**: v0 tự đoán bừa tài khoản ➔ v1/v2 tự động nhận biết thiếu handle và hỏi lại người dùng | `transcripts/v3_gemini_20260729T105438.transcript.json` |
| 3. Xác nhận an toàn trước khi đăng | `clarify(question="...", response_type="yes_no")` | **v0 ➔ v1**: v0 tự động gửi ngay không an toàn ➔ v1/v2 tuân thủ mốc an toàn, xin xác nhận yes_no | `transcripts/v3_gemini_20260729T105438.transcript.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline prompt ban đầu | Prompt cố tình đoán bừa và tự động đăng bài | case_accuracy | 0.0 | 0.65 | `runs/v0_B_base_gemini_20260729T094959034055.json` |
| v1 | Thêm quy tắc phân loại tool, clarify & boundary | Định hướng rõ quy tắc chọn tool và xác nhận giúp tăng độ chính xác | case_accuracy | 0.65 | 0.85 | `runs/v1_B_base_gemini_20260729T100334998295.json` |
| v2 | Tối ưu trích xuất từ khóa sạch & giữ ngữ cảnh multi-turn | Loại bỏ từ rác trong query và truyền ngữ cảnh giữa các lượt giúp đạt điểm tuyệt đối | case_accuracy | 0.85 | 1.00 | `runs/v2_B_base_gemini_20260729T100514471027.json` |
| v3 | Kiểm chứng tái lặp trên prompt tối ưu | Xác nhận độ ổn định tuyệt đối 100% của phiên bản v2 | case_accuracy | 1.00 | 1.00 | `runs/v3_B_base_gemini_20260729T100708405066.json` |

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R03_web_news_routing` | `wrong_tool` | `lookup(query="Tin tức AI hôm nay")` | Trích xuất query chứa từ rác ("tin tức", "hôm nay") gây sai bộ lọc | Thêm quy tắc trích xuất query sạch ("AI") và đưa "hôm nay" vào `timeframe="day"` |
| `R10_missing_handle` | `missing_info` | `timeline(screenname="sama")` | v0 tự đoán bừa tài khoản Sam Altman khi người dùng không nói rõ | Đưa quy tắc bắt buộc dùng `clarify(response_type="text")` khi thiếu handle |
| `R12_confirm_before_send` | `wrong_boundary` | `send(text="...", confirmed=True)` | v0 tự động gửi bài không xin phép | Đưa quy tắc dừng lại hỏi `clarify(response_type="yes_no")` trước khi thực hiện |

## B3. Team eval cases

Danh sách 10 case thiết kế bởi nhóm trong `data/eval_group.json` (5 Single-turn + 5 Multi-turn):

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_repo_search_python` | Tìm repository GitHub bằng ngôn ngữ Python | `repo_search(query="LLM Agent", language="python", sort="stars")` | PASS |
| `G02_repo_search_ts` | Lọc ngôn ngữ TypeScript trong repo_search | `repo_search(query="AI Agent", language="typescript")` | PASS |
| `G03_missing_repo_query` | Thiếu chủ đề tìm kiếm repo ➔ clarify | `clarify(response_type="text")` | PASS |
| `G04_confirm_telegram_post` | Yêu cầu gửi bài Telegram ➔ xin xác nhận yes_no | `clarify(response_type="yes_no")` | PASS |
| `G05_out_of_scope_recipe` | Câu hỏi nấu ăn ngoài phạm vi ➔ từ chối | `no_tool` (Refuse) | PASS |
| `G06_multiturn_clarify_repo` | Lượt 1 thiếu info ➔ lượt 2 bổ sung từ khóa gọi repo_search | `repo_search(query="RAG", language="python")` | PASS |
| `G07_multiturn_repo_sort` | Lượt 2 bổ sung tham số sort=stars | `repo_search(query="vector database", sort="stars")` | PASS |
| `G08_multiturn_switch_to_repo` | Đổi từ tìm kiếm Twitter sang tìm kiếm repo GitHub | `repo_search(query="LangChain")` | PASS |
| `G09_multiturn_confirm_publish` | Lượt 2 yêu cầu đăng bài ➔ xin xác nhận yes_no | `clarify(response_type="yes_no")` | PASS |
| `G10_multiturn_out_of_scope` | Lượt 2 hỏi viết code C++ ngoài phạm vi ➔ từ chối | `no_tool` (Refuse) | PASS |

## B4. Live chat evidence

Bằng chứng chat hội thoại thực tế được lưu tại: `transcripts/v3_gemini_20260729T105438.transcript.json`

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Turn 1: Tìm repo GitHub Python | v3 | `repo_search(query="LLM Agent", language="python")` | `transcripts/v3_gemini_20260729T105438.transcript.json` | Trả về 5 repo GitHub nổi tiếng |
| Turn 2: Tóm tắt 5 tweet mới nhất | v3 | `clarify(question="...", response_type="text")` | `transcripts/v3_gemini_20260729T105438.transcript.json` | Dừng lại hỏi xin tên tài khoản |
| Turn 3: Đăng bài báo lên Telegram | v3 | `clarify(question="...", response_type="yes_no")` | `transcripts/v3_gemini_20260729T105438.transcript.json` | Dừng lại xin xác nhận trước |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên (`repo_search`) | `tools/repo_search/tool.py` | Tìm kiếm trực tiếp open-source repos trên GitHub API theo từ khóa và ngôn ngữ | Xử lý lỗi trôi chảy khi không tìm thấy repo hoặc lỗi mạng |
| Custom Tool MD | `tools/repo_search/TOOL.md` | Định nghĩa rõ contract đầu vào, đầu ra và mục đích sử dụng | Đảm bảo mô tả rõ ràng để LLM routing đúng 100% |

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**: Các quy tắc lọc từ rác trong query, ánh xạ thời gian (hôm nay ➔ day), quy tắc hỏi lại khi thiếu thông tin và mốc xác nhận an toàn trước khi hành động.
- **Which fixes belonged in `tools.yaml`?**: Việc khai báo thêm mô tả chi tiết và các tham số cho tool mới `repo_search`.
- **Which failure needed manual review instead of automatic grading?**: Các trường hợp câu hỏi ngoài phạm vi (`out_of_scope`) khi LLM trả lời văn bản từ chối mà không gọi tool.
- **What would you improve next?**: Tích hợp thêm các bộ nhớ lưu trữ đệm (Caching) cho GitHub & Tavily API để tăng tốc độ phản hồi và tiết kiệm tài nguyên.
