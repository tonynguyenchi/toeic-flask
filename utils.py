from datetime import datetime

def calculate_time_remaining(attempt):
    """Calculate remaining time for an exam attempt in seconds"""
    if attempt.status != 'in_progress':
        return 0
    
    elapsed = datetime.utcnow() - attempt.start_time
    elapsed_seconds = int(elapsed.total_seconds())
    
    # Total exam time is 120 minutes (7200 seconds)
    return max(0, 7200 - elapsed_seconds)

def format_time(seconds):
    """Format seconds into HH:MM:SS format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def get_part_questions(part_number):
    """Get question numbers for a specific TOEIC part"""
    part_ranges = {
        1: range(1, 7),      # Part I: 1-6
        2: range(7, 32),     # Part II: 7-31  
        3: range(32, 71),    # Part III: 32-70
        4: range(71, 101),   # Part IV: 71-100
        5: range(101, 131),  # Part V: 101-130
        6: range(131, 147),  # Part VI: 131-146
        7: range(147, 201)   # Part VII: 147-200
    }
    return list(part_ranges.get(part_number, []))

def calculate_progress_percentage(answered_count, total_questions=200):
    """Calculate exam progress percentage"""
    return round((answered_count / total_questions) * 100, 1)
