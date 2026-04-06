# Debian VM Operator Runbook

Use this doc if you are setting up Agent Forge on a fresh Debian (or Ubuntu) virtual machine
and want a step-by-step walkthrough that requires no prior knowledge of the factory internals.

---

## What You Need Before You Start

- A Debian or Ubuntu VM with internet access and `sudo` access for your user
- The Agent Forge suitcase archive (one of the three formats below)
- This doc open in a separate window or printed out

You do not need to install anything before you start — the scripts handle that.

---

## Step 1 — Copy the archive into the VM

**Which format to use:**

| Format | When to use |
|--------|-------------|
| `.tar.gz` | Preferred — preserves Unix file permissions correctly |
| `.zip` | Use if the tool sending the file only handles zip |
| folder | Only if you are testing locally and did not archive |

The simplest transfer method is `scp` from your main machine:

```bash
scp agent-forge-suitcase-<timestamp>.tar.gz youruser@vm-ip:~/
```

Or copy it via a shared folder, USB, or any other method that works for your setup.

---

## Step 2 — Unpack the archive

**Important:** You can unpack the archive anywhere — the deploy script will install the factory
into `~/Projects` regardless of where you unpack it.

```bash
cd ~
tar -xzf agent-forge-suitcase-<timestamp>.tar.gz
```

If you used the `.zip` format:

```bash
unzip agent-forge-suitcase-<timestamp>.zip
```

After unpacking you will have a folder like `agent-forge-suitcase-<timestamp>/`.

---

## Step 3 — Run the one-shot setup wrapper

This is the recommended path. It runs deploy then asks if you want to install the CLIs.

```bash
cd ~/agent-forge-suitcase-<timestamp>
./_agent_forge/scripts/deploy-and-bootstrap.sh
```

What this does:

1. Copies `_agent_forge` into `~/Projects` and syncs Claude / Codex adapters  
   _(no packages installed in this step)_
2. Asks: **"Run workstation bootstrap now? [y/n]"**  
   If you say `y`, it installs development dependencies and the hosted coding CLIs you choose.  
   If you say `n`, you can run bootstrap separately later.

You will be asked which CLIs to install (Claude Code, Codex, Gemini CLI) before anything is installed.
Nothing is installed silently.

---

## Alternative: Manual two-step path

If you prefer explicit control or the wrapper fails for any reason:

```bash
# Step A: deploy the factory
cd ~/agent-forge-suitcase-<timestamp>
./_agent_forge/scripts/deploy-factory.sh

# Step B: install CLIs and authenticate (run from the deployed location)
cd ~/Projects/_agent_forge
./scripts/bootstrap-workstation.sh
```

---

## Step 4 — Authenticate the CLIs

After installation the script prints auth instructions for each CLI you selected.
Complete these before moving to the next step.

| CLI | Auth command |
|-----|-------------|
| Claude Code | `claude` — follow the browser login flow |
| Codex | `codex --login` — sign in with ChatGPT |
| Gemini CLI | `gemini` — Login with Google |

**Common Debian VM pitfalls:**

- If a browser cannot open, use Claude Code's API key auth via the Anthropic Console instead.
- If `gemini` login fails with org-entitlement errors, try: `unset GOOGLE_CLOUD_PROJECT`
- On networks with TLS inspection, add: `export NODE_USE_SYSTEM_CA=1`

---

## Step 5 — Verify the machine is ready

Check that the CLIs you installed are responding:

```bash
claude --version
codex --version   # if installed
gemini --version  # if installed
```

Check that the factory installed correctly:

```bash
python3 ~/Projects/_agent_forge/scripts/verify-agent-forge.py
```

Expected output: all lines starting with `[OK]`, no `[FAIL]` lines.

---

## Step 6 — Bootstrap your first project

```bash
cd ~/Projects/_agent_forge
./scripts/bootstrap-project.sh --name <your-project>
```

The script will:
1. Create the governed project scaffold under `~/Projects/<your-project>`
2. Automatically sync Claude adapters and Codex skills
3. Ask if you want to fill in the project definition now (mission, audience, deliverable, constraints)

You can type `y` to define the project in the terminal, or `n` to fill in `docs/CONOPS.md` later.

---

## Ready State Checklist

Before calling the machine ready, verify:

- [ ] `~/Projects/_agent_forge` exists
- [ ] `~/.claude/agents` and `~/.claude/commands` are populated (symlinks)
- [ ] `~/.codex/skills` is populated (symlinks)
- [ ] Selected CLIs respond to `--version`
- [ ] Auth completed for each selected CLI
- [ ] `verify-agent-forge.py` shows 0 failures
- [ ] At least one governed project bootstrapped under `~/Projects/`

---

## Refresh Rule

This VM holds a snapshot of the factory. When the canonical machine improves the factory:

1. Rebuild the suitcase on the canonical machine: `./scripts/factory-export.sh`
2. Copy the new archive into the VM
3. Re-run: `./deploy-and-bootstrap.sh --replace-factory --no-bootstrap`

Do not patch the VM suitcase copy by hand unless you are treating this VM as a new canonical machine.
