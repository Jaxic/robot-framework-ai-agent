# Use Cases

Detailed example scenarios showing how users interact with the Robot Framework AI Agent.

---

## 1. Compliance Status Check

### Scenario
An IT administrator needs to verify that a Windows endpoint meets BitLocker encryption requirements before a compliance audit.

### User intent
Determine whether BitLocker is properly configured without remembering Robot Framework commands or navigating XML reports.

### Example conversation

**User:** "What's our BitLocker compliance status?"

**Agent:** I'll run the BitLocker compliance test suite for you.

> The BitLocker compliance test has completed. Here are the results:
>
> **Suite: bitlocker_compliance — Status: FAIL (1/5 passed)**
>
> - [FAIL] BitLocker Is Enabled On OS Drive — Protection status is "Off", expected "On"
> - [FAIL] Encryption Method Is XTS-AES 256 — Method is "None", expected "XtsAes256"
> - [FAIL] Volume Is Fully Encrypted — Status is "FullyDecrypted", expected "FullyEncrypted"
> - [PASS] TPM Is Present And Ready
> - [FAIL] Secure Boot Is Enabled — Returned "False"
>
> **Remediation:** BitLocker is not enabled on drive C:. To fix this:
> 1. Open an elevated PowerShell prompt
> 2. Run `Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 -UsedSpaceOnly -TpmProtector`
> 3. Enable Secure Boot in BIOS/UEFI settings

### Behind the scenes
1. Agent receives the message and recognizes it as a compliance check request
2. LLM generates a `tool_call` for `ExecuteTest` with `suite_name="bitlocker_compliance"`
3. Agent POSTs to `http://127.0.0.1:8000/tools/execute` with `{"suite_name": "bitlocker_compliance"}`
4. MCP server calls `robot.run()` on `tests/bitlocker_compliance.robot`
5. Robot Framework executes 5 PowerShell commands (Get-BitLockerVolume, Get-Tpm, Confirm-SecureBootUEFI)
6. Results are parsed from `output.xml` and returned as structured JSON
7. Agent formats the tool output as a human-readable string
8. LLM generates a natural language summary with remediation steps

### Expected outcome
The user gets a clear pass/fail report with actionable remediation steps, without needing to understand Robot Framework output formats.

---

## 2. Application Deployment Verification

### Scenario
A desktop support engineer needs to confirm that required applications are installed on an endpoint after an image deployment.

### User intent
Verify the software inventory matches organizational requirements.

### Example conversation

**User:** "Check if all required applications are installed"

**Agent:** I'll run the application deployment verification tests.

> **Suite: application_deployment — Status: FAIL (3/4 passed)**
>
> - [PASS] Microsoft Office Is Installed — Microsoft 365 Apps for enterprise version 16.0.17928.20156
> - [FAIL] Adobe Acrobat Reader Is Installed — Adobe Acrobat Reader is not installed
> - [PASS] 7-Zip Is Installed — 7-Zip 24.09 (x64)
> - [PASS] Google Chrome Is Installed — Google Chrome version 131.0.6778.140
>
> Adobe Acrobat Reader is missing from this endpoint. It can be installed via your software deployment tool or downloaded from the Adobe website.

### Behind the scenes
1. LLM selects `ExecuteTest` with `suite_name="application_deployment"`
2. Robot Framework queries Windows registry uninstall keys (both 64-bit and Wow6432Node hives)
3. Each test searches for a `DisplayName` matching a regex pattern
4. Found applications report their `DisplayVersion`; missing ones fail with a descriptive message

### Expected outcome
Clear report showing which applications are present (with versions) and which are missing, without requiring the user to run PowerShell commands manually.

---

## 3. Troubleshooting Test Failures

### Scenario
A test ran earlier and failed. The user wants to understand why without reading raw XML log files.

### User intent
Root-cause analysis of a specific test failure.

### Example conversation

**User:** "Why did the Windows services test fail?"

**Agent:** Let me search the logs for failure details.

> **Found 2 matching log entries:**
>
> - [FAIL] windows_services / Windows Update Service Is Running: Windows Update service (wuauserv) is not in Running state — current status: Stopped
> - [FAIL] windows_services / Critical Services Summary: 1 of 5 critical services are not running: wuauserv (Stopped)
>
> The Windows Update service (`wuauserv`) is stopped. This is the root cause of both failures — the individual service check failed, and the summary test aggregated that failure.
>
> To fix this:
> ```powershell
> Start-Service wuauserv
> Set-Service wuauserv -StartupType Automatic
> ```

### Behind the scenes
1. LLM selects `SearchLogs` with `keyword="Stopped"` and `log_level="FAIL"`
2. Agent POSTs to `/tools/search_logs`
3. MCP server parses `output.xml` using `xml.etree.ElementTree`, searching `<msg>` elements
4. A parent map is built to determine which test suite and test case each message belongs to
5. Matching entries are returned with suite/test context

### Expected outcome
The user gets a targeted explanation of the failure cause and a remediation command, without reading through XML or HTML reports.

---

## 4. Discovering Available Tests

### Scenario
A new team member wants to understand what testing capabilities are available.

### User intent
Get an overview of the system without reading documentation.

### Example conversation

**User:** "What can you test for me?"

**Agent:**
> Here are the available test suites:
>
> - **bitlocker_compliance**: Checks BitLocker drive encryption status on the OS volume, including encryption method (XTS-AES 256), protection status, TPM readiness, and Secure Boot configuration.
>
> - **application_deployment**: Validates that required applications are installed by querying Windows registry uninstall keys. Reports the installed version for each application or fails if missing.
>
> - **windows_services**: Verifies that critical Windows services are running, including Windows Defender, Windows Update, DNS Client, Windows Firewall, and Windows Time Service.
>
> Would you like me to run any of these?

### Behind the scenes
1. LLM selects `ListTests`
2. Agent POSTs to `/tools/list_tests`
3. MCP server scans `tests/*.robot`, extracts the `Documentation` setting from each file
4. Results are returned as a list of suite names with descriptions

### Expected outcome
The user understands what tests exist and what they check, using the documentation embedded in each `.robot` file.

---

## 5. Reviewing Previous Results

### Scenario
Tests were run earlier in the day. The user wants to check results without re-running them.

### User intent
View historical results without triggering new test execution.

### Example conversation

**User:** "Show me the latest test results for Windows services"

**Agent:**
> **Suite: windows_services (from results/windows_services/output.xml)**
> **Status: FAIL — Passed: 4/6**
>
> - [PASS] Windows Defender Is Running — WinDefend service is Running
> - [FAIL] Windows Update Service Is Running — wuauserv is Stopped
> - [PASS] DNS Client Service Is Running — Dnscache is Running
> - [PASS] Windows Firewall Service Is Running — mpssvc is Running
> - [PASS] Windows Time Service Is Running — W32Time is Running
> - [FAIL] Critical Services Summary — 1 of 5 critical services are not running
>
> These results are from the last execution. Would you like me to re-run the tests to get fresh results?

### Behind the scenes
1. LLM selects `GetResults` with `suite_name="windows_services"`
2. Agent POSTs to `/tools/results`
3. MCP server finds the latest `output.xml` in `results/windows_services/`
4. `ExecutionResult` from `robot.api` parses the XML into structured data
5. Results are returned without executing any tests

### Expected outcome
The user sees previous results instantly without waiting for test execution.

---

## 6. Ad-hoc Service Check

### Scenario
The user has a specific concern about a single service and wants a quick answer.

### User intent
Check the status of a specific Windows service.

### Example conversation

**User:** "Is Windows Defender running?"

**Agent:** Let me run the Windows services check to verify.

> I ran the Windows services test suite. Here are the relevant results:
>
> - [PASS] Windows Defender Is Running — The WinDefend service is in Running state
>
> Windows Defender is active and running on this endpoint.

### Behind the scenes
1. The agent determines that the `windows_services` suite covers Defender checks
2. It calls `ExecuteTest` with `suite_name="windows_services"`
3. The full suite runs (all 6 tests), but the agent highlights only the relevant result
4. The LLM filters the response to focus on the user's specific question

### Expected outcome
The user gets a focused answer to their specific question, even though the full test suite ran behind the scenes. The agent's natural language understanding filters the relevant information.

---

## Interaction Patterns

### Single-turn queries
Most interactions are single-turn: the user asks, the agent responds. Examples:
- "What tests exist?" -> ListTests
- "Run BitLocker check" -> ExecuteTest
- "Show last results" -> GetResults

### Multi-step reasoning
Some queries require multiple tool calls:
- "Run all tests and summarize" -> ListTests, then ExecuteTest x3, then summarize
- "What's failing and why?" -> GetResults, then SearchLogs

### Conversational follow-ups
The agent handles context from previous messages:
- "Run the Windows services test" -> (agent runs test)
- "Why did it fail?" -> (agent searches logs for the suite just tested)

---

## Tips for Best Results

1. **Be specific about what you want** — "Run the BitLocker check" works better than "check my computer"
2. **Use suite names when you know them** — "Run bitlocker_compliance" is unambiguous
3. **Ask about failures after running tests** — the agent can search logs for the most recent execution
4. **Check the reasoning steps** — expand the "Agent reasoning steps" section to see which tools were called
