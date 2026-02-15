import backbone_of_code as prgrm
import codecs
import typing

if __name__ == '__main__':
    db = prgrm.DefenceDatabase()
    execute = prgrm.DataFetcher()
    db.drop_all_tables()
    db.create_tables()

# Seed defences
    sample_defences = [
        ("AUTOMATISM", 0),
        ("INSANITY", 1),
        ("SELF-DEFENCE", 0),
    ]
    for dt, essay in sample_defences:
        db.add_defence(dt, essay)

    # Map defence names to IDs for convenience
    defence_map = {d_type: d_id for (d_id, d_type, _) in execute.fetch_all_defences()}

    # Seed law (example)
    sample_law = [
        (defence_map["AUTOMATISM"], "Hill v Baxter (1958)",
         "Automatism must be caused by an external factor, e.g., being attacked by bees."),
        (defence_map["AUTOMATISM"], "R v T (1990)",
         "Exceptional stress from external trauma can trigger automatism."),
        (defence_map["AUTOMATISM"], "AG’s Ref (No.2 of 1992)",
         "Partial loss of control is not sufficient for automatism."),
    ]
    db.add_law_cases(sample_law)

    # Seed quiz
    quiz_id = db.add_quiz(defence_map["AUTOMATISM"], "Automatism Basics", quiz_link="quiz/automatism")
    q1_id = db.add_question(quiz_id, defence_map["AUTOMATISM"], "Which factor can trigger automatism?")
    db.add_answers([
        (q1_id, "External factors like a swarm of bees", 1),
        (q1_id, "Any minor distraction", 0),
        (q1_id, "Internal factors only", 0),
    ])

    # Optional: add a user and score
    user_id = db.add_user("Patrycja", "patrycja@example.com")
    db.add_score(user_id, quiz_id, 80)

    