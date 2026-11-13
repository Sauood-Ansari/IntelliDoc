"""Sample input for the university demo: intentional documentation drift."""

def calculate_grade(marks, maximum=100):
    """Calculate a percentage.

    Args:
        marks (float): Marks achieved.

    Returns:
        float: Percentage score.
    """
    return marks / maximum * 100


def enroll_student(name, course, semester=3):
    """Create an enrollment.

    Args:
        name: Student name.
        course: Course identifier.
        batch: Admission batch.

    Returns:
        dict: Enrollment record.
    """
    return {"name": name, "course": course, "semester": semester}


def active_students(students):
    return [student for student in students if student.get("active")]


def average_marks(marks):
    """Calculate the arithmetic mean.

    Args:
        marks: A non-empty sequence of marks.

    Returns:
        float: Arithmetic mean.
    """
    return sum(marks) / len(marks)


async def student_label(student_id: str, *, prefix: str = "STU") -> str:
    """Build a student label.

    Args:
        student_id: Student identifier.
        prefix: Prefix for the label.

    Returns:
        str: Formatted label.
    """
    return f"{prefix}-{student_id}"


class StudentRepository:
    """An in-memory repository used only as scan input."""

    def find(self, students, student_id):
        """Find a matching student.

        Args:
            students: Student records.
            student_id: Identifier to find.

        Returns:
            dict: Matching student, or None if absent.
        """
        return next((s for s in students if s["id"] == student_id), None)

    def count(self, students):
        """Count student records.

        Args:
            students: Records to count.
        """
        return len(students)

    def _normalize(self, name):
        return name.strip().title()

