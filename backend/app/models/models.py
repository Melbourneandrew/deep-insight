from uuid import UUID, uuid4
from typing import List, Optional

from sqlmodel import (
    Column,
    String,
    ForeignKey,
    Field,
    Relationship,
    SQLModel,
    UUID as PGUUID,
)


# ---------- Base (Pydantic) models ----------


class BusinessBase(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))


class EmployeeBase(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    email: str = Field(sa_column=Column(String(320), nullable=False))
    bio: Optional[str] = None
    business_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
        ),
    )


class QuestionBase(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    content: str
    business_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
        ),
    )
    order_index: Optional[int] = Field(default=None)
    is_follow_up: bool = Field(default=False)


class InterviewBase(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True),
    )
    business_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False
        ),
    )


class QuestionResponseBase(SQLModel):
    interview_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True), ForeignKey("interviews.id"), primary_key=True
        ),
    )
    employee_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True), ForeignKey("employees.id"), primary_key=True
        ),
    )
    question_id: UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True
        ),
    )
    content: str


# ---------- Table models (extend Base + table=True) ----------


class Business(BusinessBase, table=True):
    __tablename__ = "businesses"

    employees: List["Employee"] = Relationship(back_populates="business")
    questions: List["Question"] = Relationship(back_populates="business")
    interviews: List["Interview"] = Relationship(back_populates="business")


class Employee(EmployeeBase, table=True):
    __tablename__ = "employees"

    business: Optional[Business] = Relationship(back_populates="employees")
    responses: List["QuestionResponse"] = Relationship(back_populates="employee")


class Question(QuestionBase, table=True):
    __tablename__ = "questions"

    business: Optional[Business] = Relationship(back_populates="questions")
    responses: List["QuestionResponse"] = Relationship(back_populates="question")


class Interview(InterviewBase, table=True):
    __tablename__ = "interviews"

    business: Optional[Business] = Relationship(back_populates="interviews")
    responses: List["QuestionResponse"] = Relationship(back_populates="interview")


class QuestionResponse(QuestionResponseBase, table=True):
    __tablename__ = "responses"

    interview: Optional[Interview] = Relationship(back_populates="responses")
    employee: Optional[Employee] = Relationship(back_populates="responses")
    question: Optional[Question] = Relationship(back_populates="responses")
