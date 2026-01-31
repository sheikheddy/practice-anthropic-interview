from collections import defaultdict

class CourseSystemImpl:
    """
    Implementation of the university course registration system.
    """

    def __init__(self):
        """
        Initializes the data structures for the system.
        - self.courses: Stores course details. {course_id: (name, credit, type)}
        - self.students: Stores student credit balances. {student_id: remaining_credits}
        - self.registrations: Maps courses to registered students. {course_id: [student_id, ...]}
        - self.grades: Stores component grades. {student_id: {course_id: {component: grade}}}
        """
        self.courses = {}
        self.students = {}
        self.registrations = defaultdict(list)
        self.grades = defaultdict(lambda: defaultdict(dict))

    def create_course(self, course_id: str, course_name: str, credit: int) -> bool:
        """
        Creates a standard course. This is a convenience method for Level 1.
        """
        return self.create_course_ext(course_id, course_name, credit, "Standard")

    def register_for_course(self, student_id: str, course_id: str) -> int | None:
        """
        Registers a student for a course, checking all constraints.
        """
        # Create a new student record if they don't exist
        if student_id not in self.students:
            self.students[student_id] = 24

        # Fail if the course does not exist
        if course_id not in self.courses:
            return None

        # Fail if the student is already registered
        if student_id in self.registrations[course_id]:
            return None

        course_credit = self.courses[course_id][1]

        # Fail if the student has insufficient credits
        if self.students[student_id] < course_credit:
            return None

        # Process the registration
        self.students[student_id] -= course_credit
        self.registrations[course_id].append(student_id)

        return self.students[student_id]

    def get_paired_students(self) -> str:
        """
        Finds and formats pairs of students in the same 'Standard' courses.
        """
        all_course_pair_strings = []

        # Iterate through courses sorted by course_id for consistent output
        for course_id in sorted(self.registrations.keys()):
            # Skip non-standard courses
            if self.courses[course_id][2] != "Standard":
                continue

            students_in_course = self.registrations[course_id]
            if len(students_in_course) < 2:
                continue

            # Sort students for lexicographical pair ordering
            sorted_students = sorted(students_in_course)
            
            current_course_pairs = []
            for i in range(len(sorted_students)):
                for j in range(i + 1, len(sorted_students)):
                    pair_str = f"[{sorted_students[i]}, {sorted_students[j]}]"
                    current_course_pairs.append(pair_str)
            
            if current_course_pairs:
                all_course_pair_strings.append(f"[{', '.join(current_course_pairs)}]")

        return ", ".join(all_course_pair_strings)

    def create_course_ext(self, course_id: str, course_name: str, credit: int, grading_type: str) -> bool:
        """
        Creates a course with a specified grading type.
        """
        # Fail if course ID already exists
        if course_id in self.courses:
            return False

        # Fail if course name already exists
        for name, _, _ in self.courses.values():
            if name == course_name:
                return False

        self.courses[course_id] = (course_name, int(credit), grading_type)
        return True

    def set_component_grade(self, student_id: str, course_id: str, component: str, grade: int) -> str:
        """
        Sets or updates a grade for a specific component for a student in a course.
        """
        # Validation checks
        if student_id not in self.students:
            return "invalid"
        if course_id not in self.courses:
            return "invalid"
        if student_id not in self.registrations.get(course_id, []):
            return "invalid"

        # Determine if it's a new entry or an update
        return_status = "updated"
        if component not in self.grades[student_id][course_id]:
            return_status = "set"

        self.grades[student_id][course_id][component] = int(grade)
        return return_status

    def get_gpa(self, student_id: str) -> str | None:
        """
        Calculates a student's GPA summary based on their grades.
        """
        if student_id not in self.students:
            return None

        # Check if all registered courses have at least 3 grade components
        registered_course_ids = [cid for cid, sids in self.registrations.items() if student_id in sids]
        for cid in registered_course_ids:
            if len(self.grades[student_id].get(cid, {})) < 3:
                return None

        total_weighted_grade = 0
        total_standard_credits = 0
        pass_count = 0
        fail_count = 0

        # Calculate scores for each course
        for course_id, components in self.grades[student_id].items():
            # Only consider courses the student is still registered for
            if course_id not in registered_course_ids:
                continue

            _, credit, grading_type = self.courses[course_id]
            course_total_score = sum(components.values())

            if grading_type == "Standard":
                total_weighted_grade += course_total_score * credit
                total_standard_credits += credit
            else:  # Pass/Fail
                if course_total_score >= 66:
                    pass_count += 1
                else:
                    fail_count += 1
        
        # Calculate final weighted average
        weighted_avg = 0
        if total_standard_credits > 0:
            weighted_avg = int(total_weighted_grade / total_standard_credits)

        return f"{weighted_avg}, {pass_count}, {fail_count}"

    def find_nominee(self) -> str:
        """
        Finds department nominees based on GPA for students registered in >= 2 courses per department.
        """
        departments = sorted({course_id[:3] for course_id in self.courses.keys()})
        nominees = {}

        for department in departments:
            eligible = set()
            seen = set()
            for course_id, students in self.registrations.items():
                if not course_id.startswith(department):
                    continue
                for student_id in students:
                    if student_id in seen:
                        eligible.add(student_id)
                    seen.add(student_id)

            candidates = sorted(eligible)
            if not candidates:
                nominees[department] = ""
                continue

            best_student = candidates[0]
            best_gpa = -1
            for student_id in candidates:
                gpa = self.get_gpa(student_id)
                if gpa is None:
                    continue
                gpa_value = int(gpa.split(",")[0])
                if gpa_value > best_gpa:
                    best_gpa = gpa_value
                    best_student = student_id

            nominees[department] = best_student if best_gpa >= 0 else ""

        return ", ".join([f"{dep}({nom})" for dep, nom in nominees.items()])
