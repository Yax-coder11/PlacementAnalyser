def log_analysis(username, score, status):
    with open("analysis_log.txt", "a") as f:
        f.write(f"{username} | Score: {score} | Status: {status}\n")
