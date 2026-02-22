"""
SWARMZ V3.0 Engine Framework Test Runner
Demonstrates the multi-engine architecture in action
"""

import asyncio
import json
from datetime import datetime
from engines import engine_manager
from engines.base_engine import EngineMessage, EngineType

async def test_v3_engine_framework():
    """Test the V3.0 engine framework core functionality"""
    
    print("🚀 SWARMZ V3.0 Engine Framework Test")
    print("=" * 50)
    
    # Initialize engine manager
    print("\n📋 Initializing Engine Manager...")
    await engine_manager.initialize()
    
    # Show engine status
    print("\n🔍 Engine Status:")
    status = await engine_manager.get_system_status()
    for engine_type, engine_status in status.get("engines", {}).items():
        state = engine_status.get("state", "UNKNOWN")
        print(f"  {engine_type}: {state}")
    
    # Test Intelligence Engine
    print("\n🧠 Testing Intelligence Engine...")
    
    # Create test message
    test_message = EngineMessage(
        id="test_001",
        source_engine=EngineType.SYSTEM,  # Simulating request from system
        target_engine=EngineType.INTELLIGENCE,
        message_type="companion_chat",
        payload={
            "message": "Hello! How are you today?",
            "context": {"session_id": "test_session"}
        },
        timestamp=datetime.utcnow(),
        operator_id="test_operator"
    )
    
    # Send message to Intelligence Engine
    response = await engine_manager.route_message(test_message)
    
    if response:
        print(f"✅ Intelligence Engine Response:")
        print(f"   Message ID: {response.id}")
        print(f"   Type: {response.message_type}")
        print(f"   Payload: {json.dumps(response.payload, indent=2)}")
    else:
        print("❌ No response from Intelligence Engine")
    
    # Test Throne Protocol (Operator Sovereignty)
    print("\n👑 Testing Throne Protocol...")
    
    # Test sovereign override
    override_result = await engine_manager.throne_command(
        operator_id="test_operator",
        command="override_engine_parameter",
        target_engine=EngineType.INTELLIGENCE,
        parameters={
            "reasoning_depth": "deep",
            "ai_model_preference": "precise"
        }
    )
    
    print(f"Throne Override Result: {override_result}")
    
    # Test engine query after override
    print("\n🔄 Testing Enhanced Query with Override...")
    
    enhanced_message = EngineMessage(
        id="test_002",
        source_engine=EngineType.SYSTEM,
        target_engine=EngineType.INTELLIGENCE,
        message_type="reasoning_query",
        payload={
            "query": "Explain the concept of AI reasoning",
            "context": {"complexity": "high"}
        },
        timestamp=datetime.utcnow(),
        operator_id="test_operator"
    )
    
    enhanced_response = await engine_manager.route_message(enhanced_message)
    
    if enhanced_response:
        print(f"✅ Enhanced Response:")
        print(f"   Reasoning Mode: {enhanced_response.payload.get('reasoning_mode', 'unknown')}")
        print(f"   Confidence: {enhanced_response.payload.get('confidence', 'unknown')}")
    
    # Test health monitoring
    print("\n🏥 Health Monitor Status:")
    health = await engine_manager.get_health_status()
    print(f"  Overall Health: {health.get('overall_status', 'UNKNOWN')}")
    print(f"  Active Engines: {health.get('active_engines', 0)}")
    print(f"  Total Messages Processed: {health.get('messages_processed', 0)}")
    
    # Emergency stop test
    print("\n⚠️ Testing Emergency Stop...")
    emergency_result = await engine_manager.throne_command(
        operator_id="test_operator", 
        command="emergency_stop",
        target_engine=None  # All engines
    )
    
    print(f"Emergency Stop Result: {emergency_result}")
    
    print("\n🎯 V3.0 Framework Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_v3_engine_framework())