# Configurações Médicas Específicas por Procedimento
# Sistema Médico de Estabilidade da Cabeça

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ProcedureConfig:
    """Configuração para cada tipo de procedimento médico"""
    name: str
    sensitivity: str  # 'high', 'medium', 'low'
    stability_threshold: int  # pixels
    time_threshold: float  # segundos
    description: str
    typical_duration: str
    criticality: str  # 'critical', 'high', 'medium'

# Configurações específicas por procedimento
MEDICAL_PROCEDURES = {
    'ressonancia_magnetica': ProcedureConfig(
        name="Ressonância Magnética do Crânio",
        sensitivity='high',
        stability_threshold=5,
        time_threshold=5.0,
        description="Exame que utiliza campos magnéticos para gerar imagens detalhadas do cérebro",
        typical_duration="15-45 minutos",
        criticality='critical'
    ),
    
    'tomografia_computadorizada': ProcedureConfig(
        name="Tomografia Computadorizada da Cabeça", 
        sensitivity='medium',
        stability_threshold=8,
        time_threshold=3.0,
        description="Exame que utiliza raios-X para criar imagens seccionais da cabeça",
        typical_duration="10-30 minutos",
        criticality='high'
    ),
    
    'radiografia_craniana': ProcedureConfig(
        name="Radiografia da Cabeça (Raio-X)",
        sensitivity='medium', 
        stability_threshold=10,
        time_threshold=2.0,
        description="Exame que avalia estruturas ósseas da cabeça",
        typical_duration="2-10 minutos",
        criticality='medium'
    ),
    
    'angiografia_cerebral': ProcedureConfig(
        name="Angiografia Cerebral",
        sensitivity='high',
        stability_threshold=6,
        time_threshold=4.0,
        description="Exame dos vasos sanguíneos cerebrais",
        typical_duration="30-60 minutos",
        criticality='critical'
    ),
    
    'pet_scan_cerebral': ProcedureConfig(
        name="PET Scan Cerebral",
        sensitivity='high',
        stability_threshold=7,
        time_threshold=6.0,
        description="Tomografia por emissão de pósitrons do cérebro",
        typical_duration="45-90 minutos", 
        criticality='critical'
    ),
    
    'ultrassom_transcraniano': ProcedureConfig(
        name="Ultrassom Transcraniano",
        sensitivity='low',
        stability_threshold=15,
        time_threshold=1.5,
        description="Avaliação não invasiva dos vasos cerebrais",
        typical_duration="15-30 minutos",
        criticality='medium'
    )
}

# Configurações para populações especiais
SPECIAL_POPULATIONS = {
    'pediatrico': {
        'sensitivity_modifier': 0.8,  # Menos rigoroso
        'time_modifier': 0.7,        # Menos tempo requerido
        'feedback_frequency': 5      # Feedback mais frequente
    },
    
    'geriatrico': {
        'sensitivity_modifier': 0.9,  # Ligeiramente menos rigoroso
        'time_modifier': 0.8,        # Tempo reduzido
        'feedback_frequency': 3      # Feedback moderado
    },
    
    'neurologico': {
        'sensitivity_modifier': 0.6,  # Muito menos rigoroso
        'time_modifier': 0.5,        # Tempo muito reduzido
        'feedback_frequency': 2      # Feedback constante
    },
    
    'emergencia': {
        'sensitivity_modifier': 1.2,  # Mais rigoroso para garantir qualidade
        'time_modifier': 0.8,        # Tempo reduzido pela urgência
        'feedback_frequency': 1      # Feedback imediato
    },
    
    'padrao': {
        'sensitivity_modifier': 1.0,  # Configuração padrão
        'time_modifier': 1.0,        # Tempo padrão
        'feedback_frequency': 10     # Feedback normal
    }
}

def get_procedure_config(procedure_type: str, population: str = 'padrao') -> Dict[str, Any]:
    """
    Retorna configuração otimizada para o procedimento e população específica
    
    Args:
        procedure_type: Tipo do procedimento médico
        population: Tipo de população (pediatrico, geriatrico, neurologico, etc.)
    
    Returns:
        Dicionário com configurações otimizadas
    """
    if procedure_type not in MEDICAL_PROCEDURES:
        raise ValueError(f"Procedimento '{procedure_type}' não encontrado")
    
    base_config = MEDICAL_PROCEDURES[procedure_type]
    population_config = SPECIAL_POPULATIONS.get(population, SPECIAL_POPULATIONS['padrao'])
    
    # Aplica modificadores da população
    optimized_config = {
        'name': base_config.name,
        'sensitivity': base_config.sensitivity,
        'stability_threshold': int(base_config.stability_threshold * population_config['sensitivity_modifier']),
        'time_threshold': base_config.time_threshold * population_config['time_modifier'],
        'description': base_config.description,
        'typical_duration': base_config.typical_duration,
        'criticality': base_config.criticality,
        'feedback_frequency': population_config['feedback_frequency'],
        'population': population
    }
    
    return optimized_config

def list_available_procedures() -> Dict[str, str]:
    """Retorna lista de procedimentos disponíveis"""
    return {key: config.name for key, config in MEDICAL_PROCEDURES.items()}

def list_special_populations() -> Dict[str, str]:
    """Retorna lista de populações especiais disponíveis"""
    population_names = {
        'pediatrico': 'Pacientes Pediátricos',
        'geriatrico': 'Pacientes Geriátricos', 
        'neurologico': 'Pacientes com Condições Neurológicas',
        'emergencia': 'Casos de Emergência',
        'padrao': 'População Padrão'
    }
    return population_names

# Exemplo de uso:
if __name__ == "__main__":
    # Exemplo: Ressonância para paciente pediátrico
    config = get_procedure_config('ressonancia_magnetica', 'pediatrico')
    print(f"Configuração para {config['name']} em paciente pediátrico:")
    print(f"- Threshold: {config['stability_threshold']}px")
    print(f"- Tempo: {config['time_threshold']}s")
    print(f"- Sensibilidade: {config['sensitivity']}")
    
    print("\nProcedimentos disponíveis:")
    for key, name in list_available_procedures().items():
        print(f"- {key}: {name}")
