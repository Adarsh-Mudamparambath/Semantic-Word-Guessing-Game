from app import scoring

pairs = [("metal","iron"), ("metal","mess")]
for pair in pairs:
    secret, guess = pair
    calc_score = scoring.calculate_score(secret, guess)
    fallback = scoring._fallback_score(scoring.normalize(secret), scoring.normalize(guess))
    print(f"secret={secret!r} guess={guess!r} -> calculate_score={calc_score}, fallback={fallback}")
