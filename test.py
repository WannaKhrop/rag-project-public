"""
Module contains functions for evaluation using RAGAS Dataset.

Author: Ivan Khrop
Date: 01.06.2025
"""

from src.evaluation import run_full_test, build_test_db, run_random_test, run_one_test_sample
import logging

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ================================
# Build Test Database
# Requires 10 hours !!!
# ================================
if False:
    build_test_db(start=0, finish=250)

# ================================
# Run Random Test
# ================================
if False:
    df = run_random_test(n_samples=100, seed=42)

    # print statistics
    print(df.drop(columns="Question").mean())

    # show questions that were not answered
    not_answered = df.isnull().any(axis=1)
    if len(df[not_answered]):
        print(df[not_answered])

    # save result
    df.to_csv("RandomTestResults.csv", index=False)


# ================================
# Run Full Test
# ================================
if True:
    df = run_full_test(retrieval_only=True)

    # print statistics
    print(df.drop(columns="Question").mean())

    # show questions that were not answered
    not_answered = df.isnull().any(axis=1)
    if len(df[not_answered]):
        print(df[not_answered])

    # save result
    df.to_csv("FullTestResults.csv", index=False)


# ================================
# Show Reports for Time
# ================================
run_one_test_sample.report()
