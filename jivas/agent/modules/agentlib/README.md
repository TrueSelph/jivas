# Question Index Documentation Guide

This document provides detailed examples and patterns for creating effective question index entries to power dynamic interview functions. All examples use the `InterviewFunctionGenerator` class structure.

---

## Core Components
Every question index entry requires these core fields:

```json
"field_key": {
    "question": "Verbatim question text",
    "extraction_guidance": {
        "description": "Clear data specification",
        "type": "string|integer|date",
        "required": "Boolean",
        // Optional fields
        "examples": [],
        "validation": {},
        "fallback_phrases": [],
        "response_rules": ""
    }
}
```

## Field Types & Examples
### 1. Basic Text Response
**Use Case:** Collecting names, addresses, or free-text answers
```json
"current_medication": {
    "question": "What medications are you currently taking?",
    "extraction_guidance": {
        "description": "List of prescribed pharmaceuticals including dosage",
        "type": "string",
        "examples": ["Lisinopril 10mg daily", "Metformin 500mg twice daily"],
        "validation": {
            "pattern": "^[A-Za-z0-9\\-\\s]+(,\\s[A-Za-z0-9\\-\\s]+)*$",
            "maxLength": 500
        },
        "required": True,
        "fallback_phrases": ["I take", "My prescriptions include"]
    }
}
```

### 2. Numerical Response
**Use Case:** Ages, counts, or quantitative answers
```json
"weekly_exercise": {
    "question": "How many hours do you exercise weekly?",
    "extraction_guidance": {
        "description": "Total hours of physical activity per week",
        "type": "integer",
        "validation": {
            "minimum": 0,
            "maximum": 168
        },
        "response_rules": "Round partial hours up (e.g., '3.5' → 4)",
        "required": False
    }
}
```

### 3. Date Response
**Use Case:** Birthdates, event dates, historical timelines
```json
"last_checkup": {
    "question": "When was your last medical checkup?",
    "extraction_guidance": {
        "description": "Most recent physical examination date",
        "type": "date",
        "examples": ["2023-03-15", "2022-12-01"],
        "validation": {
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        },
        "required": True
    }
}
```

### 4. Multi-Answer Response
**Use Case:** Multiple selection or list-based answers
```json
"allergies": {
    "question": "Do you have any allergies?",
    "extraction_guidance": {
        "description": "List of known allergic substances",
        "type": "string",
        "examples": ["Penicillin, NSAIDs", "Latex, Shellfish"],
        "validation": {
            "pattern": "^[A-Za-z\\-\\s]+(,\\s[A-Za-z\\-\\s]+)*$"
        },
        "response_rules": "Convert 'none' to empty string",
        "required": False
    }
}
```

## Validation Patterns

### Text Validation

```json
"validation": {
    "minLength": 2,
    "maxLength": 100,
    "pattern": "^[A-Z][a-z]+(\\s[A-Z][a-z]+)*$" // Proper name format
}
```