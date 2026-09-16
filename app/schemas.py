import re
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA",
    "ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR",
    "PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC"
}
NAME_RE = re.compile(r"^[A-Za-z]+(?:[\-' ][A-Za-z]+)*$")
ZIP_RE = re.compile(r"^\d{5}(?:-\d{4})?$")
ALNUM_RE = re.compile(r"^[A-Za-z0-9._\- ]+$")


def normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("must be a valid U.S. 10-digit phone number")
    return digits


def parse_dob_input(value):
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
        raise ValueError("must be a valid date in MM/DD/YYYY format")
    return value


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    date_of_birth: date
    sex: Literal["Male", "Female", "Other", "Decline to Answer"]
    phone_number: str
    email: EmailStr | None = None
    address_line_1: str = Field(min_length=1, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    state: str
    zip_code: str
    insurance_provider: str | None = Field(default=None, max_length=120)
    insurance_member_id: str | None = Field(default=None, max_length=80)
    preferred_language: str | None = Field(default="English", max_length=50)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not NAME_RE.fullmatch(value):
            raise ValueError("may contain alphabetic characters, spaces, hyphens, and apostrophes only")
        return value

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_dob(cls, value):
        return parse_dob_input(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date of birth cannot be in the future")
        return value

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in US_STATES:
            raise ValueError("must be a valid 2-letter U.S. state abbreviation")
        return value

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, value: str) -> str:
        value = value.strip()
        if not ZIP_RE.fullmatch(value):
            raise ValueError("must be a 5-digit ZIP or ZIP+4")
        return value

    @field_validator("insurance_member_id")
    @classmethod
    def validate_member_id(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        value = value.strip()
        if not ALNUM_RE.fullmatch(value):
            raise ValueError("must be alphanumeric")
        return value


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    date_of_birth: date | None = None
    sex: Literal["Male", "Female", "Other", "Decline to Answer"] | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    address_line_1: str | None = Field(default=None, min_length=1, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = None
    zip_code: str | None = None
    insurance_provider: str | None = Field(default=None, max_length=120)
    insurance_member_id: str | None = Field(default=None, max_length=80)
    preferred_language: str | None = Field(default=None, max_length=50)
    emergency_contact_name: str | None = Field(default=None, max_length=120)
    emergency_contact_phone: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not NAME_RE.fullmatch(value):
            raise ValueError("may contain alphabetic characters, spaces, hyphens, and apostrophes only")
        return value

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_dob(cls, value):
        if value is None:
            return None
        return parse_dob_input(value)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date of birth cannot be in the future")
        return value

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        if value not in US_STATES:
            raise ValueError("must be a valid 2-letter U.S. state abbreviation")
        return value

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not ZIP_RE.fullmatch(value):
            raise ValueError("must be a 5-digit ZIP or ZIP+4")
        return value


class PatientRead(PatientBase):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    details: object | None = None


class Envelope(BaseModel):
    data: object | None = None
    error: ErrorBody | None = None
