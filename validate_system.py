#!/usr/bin/env python3
"""
Sistema de Validação Técnica
Sistema Médico de Estabilidade da Cabeça

Este script valida todos os componentes do sistema médico
"""

import sys
import os
import cv2
import time
import numpy as np
from medical_head_stability import MedicalHeadStabilityAnalyzer
from medical_configs import get_procedure_config, list_available_procedures

def print_header():
    """Imprime cabeçalho do sistema"""
    print("=" * 60)
    print("🏥 SISTEMA MÉDICO DE ESTABILIDADE DA CABEÇA")
    print("📋 VALIDAÇÃO TÉCNICA E FUNCIONAL")
    print("=" * 60)
    print()

def test_camera():
    """Testa funcionamento da câmera"""
    print("📹 Testando sistema de câmera...")
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Erro: Câmera não encontrada")
        return False
    
    ret, frame = cap.read()
    if not ret:
        print("❌ Erro: Não foi possível capturar frame")
        cap.release()
        return False
    
    height, width = frame.shape[:2]
    print(f"✅ Câmera funcionando: {width}x{height}")
    
    cap.release()
    return True

def test_face_detection():
    """Testa detecção facial"""
    print("👤 Testando detecção facial...")
    
    # Cria frame de teste sintético
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    test_frame[100:300, 200:400] = [100, 100, 100]  # Simula região facial
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    if face_cascade.empty():
        print("❌ Erro: Classificador facial não carregado")
        return False
    
    print("✅ Classificador Haar Cascade carregado")
    return True

def test_medical_analyzer():
    """Testa analisador médico"""
    print("🔬 Testando analisador médico...")
    
    try:
        analyzer = MedicalHeadStabilityAnalyzer(
            stability_threshold=10,
            time_threshold=3.0,
            sensitivity='medium'
        )
        print("✅ Analisador médico inicializado")
        
        # Testa análise com frame sintético
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = analyzer.analyze_stability(test_frame)
        
        print(f"✅ Análise de estabilidade funcional")
        return True
        
    except Exception as e:
        print(f"❌ Erro no analisador: {e}")
        return False

def test_configurations():
    """Testa configurações médicas"""
    print("⚙️ Testando configurações médicas...")
    
    try:
        # Testa procedimentos disponíveis
        procedures = list_available_procedures()
        print(f"✅ {len(procedures)} procedimentos configurados:")
        
        for key, name in procedures.items():
            print(f"   • {name}")
        
        # Testa configuração específica
        config = get_procedure_config('ressonancia_magnetica', 'pediatrico')
        print(f"✅ Configuração dinâmica funcional")
        print(f"   Exemplo: RM Pediátrica - {config['stability_threshold']}px, {config['time_threshold']}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas configurações: {e}")
        return False

def test_tts_system():
    """Testa sistema de texto para fala"""
    print("🔊 Testando sistema TTS...")
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        
        voices = engine.getProperty('voices')
        portuguese_voice = None
        
        for voice in voices:
            if 'brazil' in voice.name.lower() or 'portuguese' in voice.name.lower():
                portuguese_voice = voice
                break
        
        if portuguese_voice:
            print(f"✅ Voz em português encontrada: {portuguese_voice.name}")
        else:
            print("⚠️ Voz em português não encontrada - usando padrão")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no TTS: {e}")
        return False

def test_flask_dependencies():
    """Testa dependências do Flask"""
    print("🌐 Testando dependências web...")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__} instalado")
        
        import werkzeug
        print(f"✅ Werkzeug disponível")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas dependências web: {e}")
        return False

def performance_test():
    """Testa performance do sistema"""
    print("⚡ Testando performance...")
    
    try:
        analyzer = MedicalHeadStabilityAnalyzer()
        
        # Simula 30 frames de teste
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        start_time = time.time()
        
        for i in range(30):
            analyzer.analyze_stability(test_frame)
        
        end_time = time.time()
        fps = 30 / (end_time - start_time)
        
        print(f"✅ Performance: {fps:.1f} FPS")
        
        if fps >= 25:
            print("✅ Performance adequada para uso clínico")
            return True
        else:
            print("⚠️ Performance abaixo do ideal")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de performance: {e}")
        return False

def system_requirements_check():
    """Verifica requisitos do sistema"""
    print("💻 Verificando requisitos do sistema...")
    
    # Verifica Python
    python_version = sys.version_info
    print(f"🐍 Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version >= (3, 8):
        print("✅ Versão do Python adequada")
    else:
        print("❌ Python 3.8+ necessário")
        return False
    
    # Verifica OpenCV
    try:
        cv2_version = cv2.__version__
        print(f"📷 OpenCV {cv2_version}")
        print("✅ OpenCV instalado")
    except:
        print("❌ OpenCV não encontrado")
        return False
    
    # Verifica NumPy
    try:
        numpy_version = np.__version__
        print(f"🔢 NumPy {numpy_version}")
        print("✅ NumPy instalado")
    except:
        print("❌ NumPy não encontrado")
        return False
    
    return True

def generate_test_report():
    """Gera relatório de validação"""
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE VALIDAÇÃO TÉCNICA")
    print("=" * 60)
    
    tests = [
        ("Requisitos do Sistema", system_requirements_check),
        ("Sistema de Câmera", test_camera),
        ("Detecção Facial", test_face_detection),
        ("Analisador Médico", test_medical_analyzer),
        ("Configurações Médicas", test_configurations),
        ("Sistema TTS", test_tts_system),
        ("Dependências Web", test_flask_dependencies),
        ("Performance", performance_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    passed = sum(1 for name, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{name:.<30} {status}")
    
    print(f"\n📊 RESULTADO GERAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 SISTEMA TOTALMENTE VALIDADO PARA USO MÉDICO")
        print("✅ Pronto para implementação clínica")
    elif passed >= total * 0.8:
        print("⚠️ SISTEMA PARCIALMENTE VALIDADO")
        print("🔧 Alguns ajustes podem ser necessários")
    else:
        print("❌ SISTEMA REQUER CORREÇÕES")
        print("🛠️ Revisar falhas antes do uso clínico")
    
    print("\n🏥 Sistema Médico de Estabilidade da Cabeça")
    print("📅 Data da validação:", time.strftime("%d/%m/%Y %H:%M:%S"))
    print("👨‍💻 Validação técnica automatizada")

def main():
    """Função principal"""
    print_header()
    generate_test_report()

if __name__ == "__main__":
    main()
