import re
from typing import Dict, Any, List, Tuple
from config import settings

# Greenwashing indicator phrases
VAGUE_CLAIMS = [
    "eco friendly", "eco-friendly", "environmentally friendly",
    "green", "sustainable", "clean", "natural", "organic",
    "carbon neutral", "net zero", "climate positive",
    "renewable", "recyclable", "biodegradable",
]

UNSUBSTANTIATED_PATTERNS = [
    r"100%\s+(?:green|sustainable|renewable)",
    r"zero\s+(?:emissions?|carbon|footprint)",
    r"completely\s+(?:sustainable|green|eco)",
    r"(?:industry|world|global)\s+leader\s+in\s+sustainability",
]

EVIDENCE_INDICATORS = [
    r"\d+%", r"\d+\s*(?:kg|tonnes?|mt)\s*co2",
    r"(?:verified|certified)\s+by", r"according\s+to",
    r"iso\s*\d+", r"ghg\s+protocol", r"cdp", r"gri",
    r"third[\s\-]?party\s+(?:audit|verification)",
]

TRANSPARENCY_INDICATORS = [
    r"scope\s*[123]", r"baseline\s+year",
    r"methodology", r"data\s+source",
    r"emission\s+factor", r"reporting\s+period",
]

def calculate_evidence_score(text: str) -> float:
    """Calculate evidence score based on concrete data presence"""
    text_lower = text.lower()
    evidence_count = 0
    
    for pattern in EVIDENCE_INDICATORS:
        if re.search(pattern, text_lower):
            evidence_count += 1
    
    # Check for specific numbers
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    if len(numbers) > 3:
        evidence_count += 1
    
    max_score = len(EVIDENCE_INDICATORS) + 1
    return min((evidence_count / max_score) * 100, 100)

def calculate_specificity_score(text: str) -> float:
    """Calculate specificity score based on detailed claims"""
    text_lower = text.lower()
    word_count = len(text.split())
    
    # Check for specific timeframes
    has_timeframe = bool(re.search(r'(?:by|before|in)\s*\d{4}', text_lower))
    
    # Check for specific targets
    has_targets = bool(re.search(r'\d+%\s*(?:reduction|increase|improvement)', text_lower))
    
    # Check for scope mentions
    has_scopes = bool(re.search(r'scope\s*[123]', text_lower))
    
    score = 0
    if has_timeframe:
        score += 30
    if has_targets:
        score += 35
    if has_scopes:
        score += 35
    
    return score

def calculate_transparency_score(text: str) -> float:
    """Calculate transparency score"""
    text_lower = text.lower()
    transparency_count = 0
    
    for pattern in TRANSPARENCY_INDICATORS:
        if re.search(pattern, text_lower):
            transparency_count += 1
    
    max_score = len(TRANSPARENCY_INDICATORS)
    return (transparency_count / max_score) * 100

def calculate_sentiment_score(text: str) -> float:
    """Calculate sentiment balance (positive claims vs evidence)"""
    text_lower = text.lower()
    
    positive_words = len(re.findall(r'\b(?:best|leading|superior|excellent|outstanding|innovative|pioneering)\b', text_lower))
    neutral_words = len(re.findall(r'\b(?:measured|reported|calculated|assessed|evaluated|verified)\b', text_lower))
    
    if positive_words + neutral_words == 0:
        return 50
    
    balance = neutral_words / (positive_words + neutral_words)
    return balance * 100

def detect_vague_claims(text: str) -> List[Dict[str, Any]]:
    """Detect vague environmental claims without evidence"""
    text_lower = text.lower()
    flags = []
    
    for claim in VAGUE_CLAIMS:
        pattern = rf'\b{re.escape(claim)}\b'
        matches = list(re.finditer(pattern, text_lower))
        
        for match in matches:
            # Check if there's a number within 50 characters
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text_lower[context_start:context_end]
            
            has_evidence = bool(re.search(r'\d+(?:\.\d+)?%?', context))
            
            if not has_evidence:
                flags.append({
                    "type": "vague_claim",
                    "phrase": claim,
                    "context": text[context_start:context_end],
                    "severity": "medium",
                    "recommendation": f"Add specific metrics or data to support the '{claim}' claim"
                })
    
    return flags

def detect_unsubstantiated_claims(text: str) -> List[Dict[str, Any]]:
    """Detect absolute or unsubstantiated claims"""
    text_lower = text.lower()
    flags = []
    
    for pattern in UNSUBSTANTIATED_PATTERNS:
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            flags.append({
                "type": "unsubstantiated_claim",
                "phrase": match.group(),
                "context": text[max(0, match.start()-30):min(len(text), match.end()+30)],
                "severity": "high",
                "recommendation": "Absolute claims require third-party verification and detailed evidence"
            })
    
    return flags

def calculate_credibility_score(evidence: float, specificity: float, transparency: float, sentiment: float) -> float:
    """Calculate overall credibility score"""
    weights = {
        "evidence": 0.35,
        "specificity": 0.25,
        "transparency": 0.25,
        "sentiment": 0.15,
    }
    
    score = (
        evidence * weights["evidence"] +
        specificity * weights["specificity"] +
        transparency * weights["transparency"] +
        sentiment * weights["sentiment"]
    )
    
    return round(score, 2)

def determine_risk_level(credibility_score: float, flags: List[Dict]) -> str:
    """Determine risk level based on score and flags"""
    high_severity_count = sum(1 for f in flags if f.get("severity") == "high")
    
    if credibility_score < 30 or high_severity_count > 2:
        return "high"
    elif credibility_score < 60 or high_severity_count > 0:
        return "medium"
    else:
        return "low"

def generate_recommendations(flags: List[Dict], scores: Dict[str, float]) -> List[str]:
    """Generate recommendations based on analysis"""
    recommendations = []
    
    if scores["evidence"] < 50:
        recommendations.append("Include specific metrics and quantitative data to support environmental claims")
    
    if scores["specificity"] < 50:
        recommendations.append("Add specific timeframes, targets, and scope definitions to claims")
    
    if scores["transparency"] < 50:
        recommendations.append("Improve transparency by disclosing methodology, data sources, and reporting standards")
    
    if scores["sentiment"] < 50:
        recommendations.append("Balance promotional language with factual, measured statements")
    
    # Add flag-specific recommendations
    unique_recs = set()
    for flag in flags:
        if flag.get("recommendation"):
            unique_recs.add(flag["recommendation"])
    
    recommendations.extend(list(unique_recs)[:3])
    
    return recommendations[:5]

def analyze_greenwashing(text: str, use_ai: bool = False) -> Dict[str, Any]:
    """Main function to analyze document for greenwashing"""
    # Calculate scores
    evidence_score = calculate_evidence_score(text)
    specificity_score = calculate_specificity_score(text)
    transparency_score = calculate_transparency_score(text)
    sentiment_score = calculate_sentiment_score(text)
    
    scores = {
        "evidence": evidence_score,
        "specificity": specificity_score,
        "transparency": transparency_score,
        "sentiment": sentiment_score,
    }
    
    # Detect flags
    flags = []
    flags.extend(detect_vague_claims(text))
    flags.extend(detect_unsubstantiated_claims(text))
    
    # Calculate overall score
    credibility_score = calculate_credibility_score(
        evidence_score, specificity_score, transparency_score, sentiment_score
    )
    
    # Determine risk level
    risk_level = determine_risk_level(credibility_score, flags)
    
    # Generate recommendations
    recommendations = generate_recommendations(flags, scores)
    
    return {
        "credibility_score": credibility_score,
        "risk_level": risk_level,
        "flags": flags,
        "recommendations": recommendations,
        "evidence_score": evidence_score,
        "specificity_score": specificity_score,
        "transparency_score": transparency_score,
        "sentiment_score": sentiment_score,
    }
