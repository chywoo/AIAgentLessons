# AI Agent 한국어 학습 자료

이 대화에서 제작한 복습집·내부 교육 자료·개발 참고서를 모았습니다. 게시일: 2026-10-22.

| 파일 | 내용 | 사용 방법 |
|---|---|---|
| [AI_AGENT_SUMMARY_KO.md](AI_AGENT_SUMMARY_KO.md) | Markdown 복습집 | GitHub에서 읽거나 다운로드 |
| [AI_AGENT_SUMMARY_KO.html](AI_AGENT_SUMMARY_KO.html) | 단일 파일 인터랙티브 복습집 | 다운로드한 파일을 웹 브라우저에서 열기 |
| [AI_AGENT_INTERNAL_TRAINING_KO.pptx](AI_AGENT_INTERNAL_TRAINING_KO.pptx) | 사내 교육용 슬라이드 72장·발표자 노트 | 다운로드 후 PowerPoint 등에서 열기 |
| [AI_AGENT_TRAINING_LABS_KO.zip](AI_AGENT_TRAINING_LABS_KO.zip) | 교육 실습·정답·fixture·고정 의존성 | 압축을 풀고 README_KO.md 참고 |
| [AI_AGENT_REFERENCE_BOOK_KO.md](AI_AGENT_REFERENCE_BOOK_KO.md) | 본문 15장·구현 레시피 14개·연동 가이드 8개·부록 | 문제 색인으로 탐색; 코드 추출·실행은 A06 참고 |
| [ai_agent_delivery_test.txt](ai_agent_delivery_test.txt) | 최초 파일 전달 기능 확인용 파일 | 텍스트 파일 |

HTML은 GitHub 파일 미리보기에서 JavaScript가 실행되지 않습니다. 파일 화면의 다운로드 버튼으로 저장한 뒤 브라우저에서 여세요. 다른 PC에서도 저장소를 clone하거나 필요한 파일만 다운로드할 수 있습니다.

## 검증 기록

- 게시 파일 6개는 제작 완료 원본과 SHA-256이 일치합니다. ZIP·PPTX 내부 압축 무결성도 확인했습니다.
- Reference Book은 문서에서 추출한 코드로 자동 테스트 **68개 통과**, 내부 링크 **232개** 확인을 마쳤습니다.
- 교육 실습 정답은 제작 시 새 가상환경에서 **13개 테스트 통과**를 확인했습니다. 자세한 범위는 ZIP 안의 VALIDATION_KO.md에 있습니다.
- 로컬 SQLite·MCP·Qdrant 및 모의 응답의 검증과 실제 모델·외부 업무 서비스 검증을 각 자료에서 구분합니다. 실제 모델 추론·Email 발송·운영 서버 배포를 완료한 자료는 아닙니다.
- Reference Book G15–G16과 서버 심화 항목은 후속 확장 설계입니다.

무결성 확인(Linux):

```bash
cd docs/generated
sha256sum -c SHA256SUMS
```

설계와 검증 기록은 각 파일의 제작 시점을 기준으로 합니다. 문서 안의 “GitHub에 업로드하지 않았다”는 문구는 제작 완료 당시의 기록이며, 이 폴더는 이후 사용자의 업로드 요청으로 게시한 원본 보관본입니다.

가상환경, 캐시, 화면 렌더링 결과, 임시 빌드·검증 디렉터리, 로컬 설정·자격 증명은 게시 자료에 포함하지 않습니다. 실습 소스는 ZIP에, 참고서 예제 전체 소스는 Markdown에 수록되어 있습니다.
