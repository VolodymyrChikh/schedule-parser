import re
from typing import List, Dict, Optional, Any

# This will hold the globally parsed data to avoid re-parsing on every call
PARSED_SCHEDULE: Optional[List[Dict[str, Any]]] = None


def load_schedule_from_file(filepath: str) -> str:
    """
    Reads the schedule content from a plain text file.

    It is crucial that the source .doc file is saved as a .txt file
    with UTF-8 encoding for this function to work correctly.

    Args:
        filepath: The path to the .txt file.

    Returns:
        The content of the file as a single string, or an empty string on error.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # The .doc file contains BELL characters () for table cells.
            # We replace them with '\a' for Python to process.
            return f.read().replace('', '\a')
    except FileNotFoundError:
        print(f"---")
        print(f"❌ ERROR: The file '{filepath}' was not found.")
        print(f"👉 Please make sure you have saved your schedule as a .txt file")
        print(f"   in the same directory as this script.")
        print(f"---")
        return ""
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return ""


def parse_class_details(text: str) -> Dict[str, Any]:
    """
    Parses the raw text of a class cell into a structured dictionary.
    """
    text = text.strip()

    teacher_pattern = r"(?:проф|доц|ас)\.[\s\S]*"
    teachers_match = re.search(teacher_pattern, text, re.IGNORECASE)

    teachers_raw = ""
    if teachers_match:
        teachers_raw = teachers_match.group(0)
        text = text[:teachers_match.start()]

    teachers = [t.strip().replace('\n', '') for t in teachers_raw.split(',') if t.strip()]

    match = re.match(r"^(.*?)\s*\((.*?)\)$", text, re.DOTALL)

    subject = text
    details = ""
    if match:
        subject = match.group(1).strip()
        details = match.group(2).strip()

    details_parts = [p.strip() for p in details.split(',')]
    class_type = details_parts[0] if details_parts else "N/A"

    location_info = [p for p in details_parts[1:] if p]

    if '(' not in text and ')' not in text and not teachers:
        subject = text.strip()

    return {
        'subject': subject.replace('\n', ' ').replace('\x0b', ' ').strip(),
        'type': class_type,
        'location': ', '.join(location_info).replace('\n', ' ').strip(),
        'teachers': teachers
    }


def parse_full_schedule(content: str) -> List[Dict[str, Any]]:
    """
    Parses the entire schedule document from a raw string.
    """
    cells = content.split('\a')

    try:
        header_start_index = cells.index('Дні')
    except ValueError:
        print("❌ ERROR: Could not find the table header 'Дні' in the file. The file might be in the wrong format.")
        return []

    group_cells = cells[header_start_index + 2:]

    groups = []
    for cell in group_cells:
        clean_cell = cell.strip()
        # Header text can sometimes get merged, so we stop at the first non-group-like text
        if clean_cell and "Розклад" not in clean_cell and "Понеділок" not in clean_cell:
            groups.append(clean_cell)
        else:
            break

    num_groups = len(groups)
    num_cols = num_groups + 2

    data_start_index = header_start_index + num_cols

    schedule_data = []
    current_day = "N/A"

    for i in range(data_start_index, len(cells) - num_cols + 1, num_cols):
        row_cells = cells[i: i + num_cols]

        day_cell = row_cells[0].strip()
        if day_cell:
            current_day = day_cell

        pair_cell = row_cells[1].strip().replace('\n', ' ')

        for group_index, class_cell_text in enumerate(row_cells[2:]):
            class_cell_text = class_cell_text.strip()
            if class_cell_text:
                class_details = parse_class_details(class_cell_text)
                schedule_data.append({
                    'day': current_day,
                    'pair': pair_cell,
                    'group': groups[group_index],
                    **class_details
                })

    return schedule_data


def get_schedule(
        filepath: str,
        group: str,
        day_of_week: str,
        numerator_denominator: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Loads, parses, and retrieves the schedule for a specific group and day.

    Args:
        filepath (str): The path to the schedule .txt file.
        group (str): The name of the group (e.g., "ПМІ – 21с").
        day_of_week (str): The day of the week (e.g., "Понеділок").
        numerator_denominator (Optional[str]): Not used for filtering but included per request.

    Returns:
        A list of dictionaries for the specified query.
    """
    global PARSED_SCHEDULE

    if PARSED_SCHEDULE is None:
        content = load_schedule_from_file(filepath)
        if not content:
            return []
        print("Parsing schedule for the first time...")
        PARSED_SCHEDULE = parse_full_schedule(content)
        print("Parsing complete.")

    if numerator_denominator is not None:
        print("\nNote: The 'numerator_denominator' parameter is ignored as this data is not in the source file.")

    results = []
    for entry in PARSED_SCHEDULE:
        if (entry['group'].strip().lower() == group.strip().lower() and
                entry['day'].strip().lower() == day_of_week.strip().lower()):
            results.append(entry)

    return results


# --- Example Usage ---
if __name__ == "__main__":
    # The script will look for a file with this name.
    # Make sure your saved .txt file matches this name or change the variable.
    schedule_filename = "D://schedule-parser//schedules//Розклад_2022_2023_І_семестр_Інф_ІІ_курс.txt"

    # --- Query 1 ---
    print("--- Query 1: Group ПМІ–26с on Monday ---")
    my_group = "ПМІ – 26с"
    my_day = "Понеділок"
    schedule = get_schedule(schedule_filename, my_group, my_day)

    if schedule:
        for cls in schedule:
            print(f"\n📚 Пара: {cls['pair']}")
            print(f"   Предмет: {cls['subject']} ({cls['type']})")
            print(f"   Аудиторія: {cls['location']}")
            print(f"   Викладачі: {', '.join(cls['teachers'])}")
    else:
        print(f"No classes found for group '{my_group}' on '{my_day}'.")

    print("\n" + "=" * 50 + "\n")

    # --- Query 2 ---
    print("--- Query 2: Group ПМІ – 21с on Friday ---")
    my_group_2 = "ПМІ – 21с"
    my_day_2 = "П’ятниця"
    schedule_2 = get_schedule(schedule_filename, my_group_2, my_day_2)

    if schedule_2:
        for cls in schedule_2:
            print(f"\n📚 Пара: {cls['pair']}")
            print(f"   Предмет: {cls['subject']} ({cls['type']})")
            print(f"   Аудиторія: {cls['location']}")
            print(f"   Викладачі: {', '.join(cls['teachers'])}")
    else:
        print(f"No classes found for group '{my_group_2}' on '{my_day_2}'.")