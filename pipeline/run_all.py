"""
Rebuild everything from scratch, deterministically (fixed seed):
data -> quality gate -> model -> metrics -> planning -> launch -> docs -> memo -> market -> web app.

Run from the repo root:  python pipeline/run_all.py
"""
import importlib
import time

STEPS = [
    ("generate_data", "Simulating accounts, territories, and three years of deals"),
    ("validate", "Running the data-quality gate"),
    ("propensity_model", "Training the propensity model and scoring whitespace"),
    ("metrics", "Computing reference metrics"),
    ("planning", "Running the FY27 capacity model"),
    ("launch", "Building the Prisma Browser launch scorecard"),
    ("content", "Writing the operating-cadence docs"),
    ("write_memo", "Writing the executive memo (Markdown and one-page PDF)"),
    ("write_docs", "Writing the launch kit and methodology"),
    ("market", "Building the market context from real public data"),
    ("build_app", "Assembling the self-contained index.html"),
]


def main():
    start = time.time()
    for module, label in STEPS:
        print(f"\n== {label} ({module}.py)")
        mod = importlib.import_module(module)
        (mod.write_docs if module == "content" else mod.main)()
    print(f"\nDone in {time.time() - start:.0f}s. Open index.html in a browser.")


if __name__ == "__main__":
    main()
