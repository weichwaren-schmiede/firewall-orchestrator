from typing import Final


class Person:
    species: str = "Homo sapiens"
    gender: str

    def __init__(self, height: float, eye_color: str) -> None:
        self.height: float = height
        self.eye_color: str = eye_color

    def speak(self, message: str) -> None:
        print(f"Person says: {message}")

    def describe(self) -> None:
        print(f"Person is {self.height} cm tall and has {self.eye_color} eyes. and species: {self.species}")


# Example usage


person1: Final[Person] = Person(180.0, "blue")
print(person1.__dict__)
person1.describe()

Person.species = "Ape"

person1.describe()

person1.species = "enrite"


person2 = Person(170.0, "green")
person2.describe()
person1.describe()

Person.species = "Ape????"
person2.describe()
person1.describe()
print(person1.__dict__)
print(person2.__dict__)
