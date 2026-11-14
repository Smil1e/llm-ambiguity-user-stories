"""Central settings for the experiment. Change values here, not inside the scripts."""
import os

SEED = 42                 # fixed seed -> the same stories and injections every time
N_BASE = 50               # presumed-clean base stories (full experiment)
N_PILOT = 5               # base stories in the pilot (5 originals + 15 injected)
N_TEST_PROJECTS = 3       # projects the test stories are drawn from
N_RUNS = 2                # repetitions per story / model / strategy
RETRY_INVALID = 2         # fixed BEFORE the experiment: re-ask up to 2 times if the reply is not valid

TEMPERATURE = 0.0
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))  # generous: some models spend tokens on internal reasoning

# Model names. Check the provider's current model list before running and set these
# environment variables if the defaults are not available to you.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")  # REQUIRED for Gemini, e.g. export GEMINI_MODEL=<current flash model>
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")  # REQUIRED for OpenAI, e.g. export OPENAI_MODEL=<current small GPT model>
OPENAI_REASONING = os.getenv("OPENAI_REASONING", "none")  # reasoning effort for reasoning models; "" to omit

# The three lexical ambiguity types studied.
TYPES = ["vague_qualifier", "vague_quantifier", "escape_clause"]
VOCAB_GROUPS = ["in", "out"]

DATA_DIR = "data"
RESULTS_DIR = "results"
