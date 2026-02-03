# Demo Script

A step-by-step walkthrough for demonstrating the Robot Framework AI Agent. Follow this script to deliver a compelling demo that shows the value of AI-powered test automation.

---

## Demo Preparation

### Services to start

Open three terminal windows (each with the venv activated):

```bash
# Terminal 1 — Ollama (if not already running)
ollama serve

# Terminal 2 — MCP Server
cd X:\Robot_Framework\robot-framework-ai-agent
venv\Scripts\activate
python -m mcp_server.server

# Terminal 3 — Streamlit UI
cd X:\Robot_Framework\robot-framework-ai-agent
venv\Scripts\activate
streamlit run ui/app.py
```

### Pre-demo checklist

- [ ] Ollama is running and the model is loaded (`ollama list` shows `qwen2.5:32b-instruct-q4_k_m`)
- [ ] MCP server is running (check `http://127.0.0.1:8000/health`)
- [ ] Streamlit UI is open in the browser at `http://localhost:8501`
- [ ] Both status indicators in the sidebar show green
- [ ] Chat history is cleared (click "Clear Chat" in sidebar)
- [ ] Have a Robot Framework `.robot` file open in an editor for reference

### Optional: prepare a failure scenario

To demonstrate troubleshooting, stop a Windows service beforehand:

```powershell
# Run as Administrator
Stop-Service wuauserv
```

This will cause the Windows services test to fail, which makes Act 4 more compelling.

---

## Demo Flow

### Act 1: The Problem (2 minutes)

**Talking points:**

> "Compliance testing is critical but tedious. Today, checking if an endpoint meets security policy means either running command-line tools and reading XML output, or navigating complex dashboards."

Show a raw `output.xml` file briefly to illustrate the complexity:

> "Here's what a Robot Framework test result looks like. It's comprehensive, but not something you'd want to read through at 9 AM on a Monday."

Then show the Streamlit UI:

> "What if you could just ask a question in plain English and get an instant, actionable answer? That's what this project does."

---

### Act 2: Discovery (3 minutes)

**Action:** Type or click the example button: **"What tests are available?"**

**Wait for response.** The agent will call the `ListTests` tool and return descriptions of all three test suites.

**Talking points:**

> "I just asked a simple question. Behind the scenes, the AI agent decided to call the `ListTests` tool, which scanned the `tests/` directory for Robot Framework files and extracted their documentation."

**Show the reasoning steps** by expanding the "Agent reasoning steps" section:

> "You can see exactly what the agent did — it called the `ListTests` tool and got back the suite descriptions. There's no magic black box here; every decision is transparent."

**Key message:** The AI understands natural language and translates it into the right tool call automatically.

---

### Act 3: Test Execution (5 minutes)

**Action:** Type: **"Run the Windows services check"**

**Wait for response.** This takes 10-30 seconds as Robot Framework executes PowerShell commands.

**While waiting, explain:**

> "Right now, the agent sent the request to our MCP server, which is executing the Robot Framework test suite. Each test runs a PowerShell command to check a Windows service — Defender, Windows Update, DNS, Firewall, and Time Service."

**When results appear:**

> "The agent ran 6 tests and gave us a clear summary. No XML parsing, no report navigation — just a plain English answer with pass/fail status for each service."

If the `wuauserv` service was stopped in preparation:

> "Notice that Windows Update failed. The agent tells us exactly what's wrong: the `wuauserv` service is stopped."

**Show the Swagger UI** (optional): Open `http://127.0.0.1:8000/docs` in another tab:

> "The MCP server also has a full REST API with interactive documentation. This means other tools and scripts can call these same endpoints."

---

### Act 4: Troubleshooting (3 minutes)

**Action:** Type: **"Why did the services test fail?"**

**Wait for response.** The agent will call `SearchLogs` to find FAIL entries.

**Talking points:**

> "Instead of opening `log.html` and searching through test output, I just asked the agent to investigate. It searched the execution logs, found the specific FAIL messages, and identified the root cause."

> "It even suggests the fix: `Start-Service wuauserv`. This is the kind of actionable intelligence that saves time for IT teams."

**If you stopped the service earlier, fix it now:**

```powershell
Start-Service wuauserv
```

**Then ask:** "Run the Windows services check again"

> "Now all 6 tests pass. The agent confirms everything is healthy."

---

### Act 5: Wrap-up and Q&A (2 minutes)

**Talking points:**

> "Let me recap what we just did:
> 1. Discovered available tests using natural language
> 2. Executed a compliance check by asking for it
> 3. Got instant, actionable results
> 4. Investigated a failure and got a remediation suggestion
> 5. Verified the fix
>
> All without writing a single command or reading an XML file."

---

## Anticipated Questions and Answers

### "Is this secure? Where does the data go?"

> Everything runs locally. The LLM runs on Ollama on this machine. The MCP server binds to localhost only. No data is sent to any cloud service. There are no API keys involved.

### "Can we add our own tests?"

> Yes. Drop a `.robot` file into the `tests/` directory and it's automatically discovered. The MCP server scans the directory at runtime. You don't need to change any code.

### "Does it work with cloud LLMs like GPT-4 or Claude?"

> Yes. Change two lines in `agent/llm_config.py` to switch from Ollama to OpenAI, Anthropic, or any LangChain-supported provider. The rest of the architecture stays the same.

### "How fast is it?"

> The bottleneck is the LLM inference. With a GPU, responses come in 5-15 seconds. Without a GPU, expect 30-60 seconds for the 32B model. You can use a smaller model for faster responses at the cost of some reasoning quality.

### "Can this scale to multiple endpoints?"

> The current architecture is single-endpoint. For fleet-wide deployment, you'd deploy the MCP server on each endpoint and add a central orchestrator. The modular architecture makes this straightforward.

### "What about other operating systems?"

> The test suites are Windows-specific (PowerShell commands), but the architecture is OS-agnostic. You could write Linux test suites that use shell commands instead of PowerShell. The agent, MCP server, and UI work on any platform.

### "How does it decide which tool to use?"

> The LLM receives a system prompt describing each tool's purpose. Based on the user's question, it generates a structured tool call. For example, "run the BitLocker check" maps to `ExecuteTest`, while "show recent failures" maps to `GetResults`. The reasoning is visible in the expandable "Agent reasoning steps" section.

---

## Follow-up Materials

After the demo, share:

1. **GitHub repository** — full source code and documentation
2. **README.md** — quick start guide for setting up their own instance
3. **docs/ARCHITECTURE.md** — technical deep-dive for engineering teams
4. **docs/USE_CASES.md** — additional scenarios and interaction patterns

---

## Troubleshooting During Demo

### Agent takes too long

- The model might be loading for the first time. Subsequent queries will be faster.
- Check the Ollama terminal for progress indicators.
- If consistently slow, consider using a smaller model for the demo.

### MCP server returns errors

- Check Terminal 2 for error messages.
- Verify with `curl http://127.0.0.1:8000/health`.
- Common issue: the server was started from the wrong directory. It must run from the project root.

### Streamlit shows "MCP Server" in red

- The MCP server isn't running or crashed. Restart it in Terminal 2.
- The health check runs on every page load, so refresh the page after restarting.

### Test execution fails with permission errors

- BitLocker tests require administrator privileges.
- For the demo, use the `windows_services` or `application_deployment` suites which don't need elevation.
