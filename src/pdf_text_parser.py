"""
Simple text parser to extract structured data from PDF content when LLM is not available.
"""

import re
from typing import Dict, List, Any

def parse_pdf_text(pdf_text: str, condition_name: str) -> Dict[str, Any]:
    """Parse PDF text to extract structured information."""
    
    result = {
        "condition": condition_name,
        "cid_10": [],
        "medicamentos": [],
        "documentos_pessoais": [],
        "documentos_medicos": [],
        "exames": [],
        "observacoes": [],
        "extraction_method": "text_parser"
    }
    
    if not pdf_text.strip():
        return result
    
    lines = pdf_text.split('\n')
    
    # Extract CID-10 codes
    for line in lines:
        # Look for CID-10 pattern in lines like "ACNE GRAVE – CID-10: L70.0, L70.1 e L70.8"
        cid_match = re.search(r'CID-10:\s*([A-Z]\d{2}(?:\.\d)?(?:\s*,\s*[A-Z]\d{2}(?:\.\d)?)*(?:\s*e\s*[A-Z]\d{2}(?:\.\d)?)*)', line)
        if cid_match:
            cid_text = cid_match.group(1)
            # Split by comma and 'e'
            cids = re.split(r'\s*,\s*|\s*e\s*', cid_text)
            result["cid_10"].extend([cid.strip() for cid in cids if cid.strip()])
    
    # Extract medications
    in_medications_section = False
    for line in lines:
        line = line.strip()
        
        if line.upper().startswith('MEDICAMENTOS'):
            in_medications_section = True
            continue
        
        if in_medications_section:
            # Stop when we hit another section
            if line.upper().startswith('DOCUMENTOS') or line.upper().startswith('EXAMES') or line.upper().startswith('OBSERVAÇÕES'):
                in_medications_section = False
                continue
            
            # Extract medication names (usually start with a bullet point or are on their own line)
            if line and not line.startswith(' ') and len(line) > 3:
                # Clean up the line - remove bullet points and extra formatting
                medication = re.sub(r'^[•\-\s]*', '', line)
                medication = re.sub(r'\s*;\s*$', '', medication)  # Remove trailing semicolon
                
                if medication and len(medication) > 2:  # Skip very short lines
                    result["medicamentos"].append(medication)
    
    # Extract personal documents
    in_personal_docs = False
    for line in lines:
        line = line.strip()
        
        if 'DOCUMENTOS PESSOAIS' in line.upper():
            in_personal_docs = True
            continue
        
        if in_personal_docs:
            if line.upper().startswith('DOCUMENTOS A SEREM EMITIDOS') or line.upper().startswith('EXAMES'):
                in_personal_docs = False
                continue
            
            if line and len(line.strip()) > 5:
                doc = line.strip()
                doc = re.sub(r'^[•\-\s]*', '', doc)
                if doc and not doc.upper().startswith('DOCUMENTOS') and not doc.upper().startswith('PRIMEIRA'):
                    result["documentos_pessoais"].append(doc)
    
    # Extract medical documents
    in_medical_docs = False
    for line in lines:
        line = line.strip()
        
        if 'DOCUMENTOS A SEREM EMITIDOS PELO MÉDICO' in line.upper():
            in_medical_docs = True
            continue
        
        if in_medical_docs:
            if line.upper().startswith('EXAMES') or line.upper().startswith('OBSERVAÇÕES'):
                in_medical_docs = False
                continue
            
            if line and len(line.strip()) > 5:
                doc = line.strip()
                doc = re.sub(r'^[•\-\s]*', '', doc)
                if doc and not doc.upper().startswith('PRIMEIRA') and not doc.upper().startswith('RENOVAÇÃO') and not doc.upper().startswith('DOCUMENTOS'):
                    result["documentos_medicos"].append(doc)
    
    # Extract exams
    in_exams = False
    for line in lines:
        line = line.strip()
        
        if 'EXAMES A SEREM APRESENTADOS' in line.upper():
            in_exams = True
            continue
        
        if in_exams:
            if line.upper().startswith('OBSERVAÇÕES') or line.upper().startswith('ATENÇÃO'):
                in_exams = False
                continue
            
            if line and len(line.strip()) > 5:
                exam = line.strip()
                exam = re.sub(r'^[•\-\s]*', '', exam)
                if exam and not exam.upper().startswith('PRIMEIRA') and not exam.upper().startswith('RENOVAÇÃO') and not exam.upper().startswith('EXAMES'):
                    result["exames"].append(exam)
    
    # Extract observations
    in_observations = False
    for line in lines:
        line = line.strip()
        
        if line.upper().startswith('OBSERVAÇÕES') or line.upper().startswith('ATENÇÃO'):
            in_observations = True
            if line.startswith(' '):  # If the observation starts on the same line
                obs = line
                obs = re.sub(r'^[•\-\s]*', '', obs)
                if obs:
                    result["observacoes"].append(obs)
            continue
        
        if in_observations:
            if line and len(line.strip()) > 5:
                obs = line.strip()
                obs = re.sub(r'^[•\-\s]*', '', obs)
                if obs:
                    result["observacoes"].append(obs)
    
    # Clean up empty entries
    for key in result:
        if isinstance(result[key], list):
            result[key] = [item for item in result[key] if item and len(item.strip()) > 2]
    
    return result

def test_parser():
    """Test the parser with sample data."""
    sample_text = """RELAÇÃO DE DOCUMENTOS E EXAMES PARA SOLICITAÇÃO DE
MEDICAMENTO(S)
ACNE GRAVE – CID-10: L70.0, L70.1 e L70.8
MEDICAMENTOS
 Isotretinoína 20 mg – Cápsula
DOCUMENTOS PESSOAIS A SEREM APRESENTADOS
 Cópia da Carteira de Identidade (ou Documento de Identificação com foto)
 Cópia do Cartão Nacional de Saúde (CNS)
 Cópia do Comprovante de Residência
DOCUMENTOS A SEREM EMITIDOS PELO MÉDICO
PRIMEIRA SOLICITAÇÃO
 LME - Laudo de Solicitação, Avaliação e Autorização de Medicamentos (Modelo Anexo)
 Prescrição Médica
EXAMES A SEREM APRESENTADOS
PRIMEIRA SOLICITAÇÃO: EXAMES GERAIS
 Cópia do exame de dosagem sérica de Triglicerídeos (válido 6 meses);
 Cópia do exame de dosagem de ALT/TGP (válido 6 meses);
OBSERVAÇÕES
 ATENÇÃO: No que tange os documentos sob a responsabilidade do médico devem ser providenciados por DERMATOLOGISTA.
 Isotretinoína: Medicamentos sujeitos a controle especial"""

    result = parse_pdf_text(sample_text, "Acne Grave")
    
    print("🧪 Testing PDF Text Parser")
    print("=" * 30)
    print(f"CID-10: {result['cid_10']}")
    print(f"Medications: {result['medicamentos']}")
    print(f"Personal docs: {len(result['documentos_pessoais'])}")
    print(f"Medical docs: {len(result['documentos_medicos'])}")
    print(f"Exams: {len(result['exames'])}")
    print(f"Observations: {len(result['observacoes'])}")

if __name__ == "__main__":
    test_parser()