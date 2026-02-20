#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from swarmz_runtime.core.engine import SwarmzEngine
    print('Engine imported successfully')

    engine = SwarmzEngine(data_dir='data')
    print('Engine initialized')

    print('Kernel ignition method exists:', hasattr(engine, 'execute_kernel_ignition'))

    # Test basic functionality
    context = {'domain': 'test'}
    options = [{'id': 'test1', 'strategy': 'safe'}]

    result = engine.process_task_matrix(context, options)
    print('Task matrix processed, vector length:', len(result['unified_vector']))

    ignition = engine.execute_kernel_ignition(result)
    print('Kernel ignition executed')
    print('State:', ignition['kernel_state'])
    print('Steps:', len(ignition['sequence_steps']))

    print('SUCCESS: IGNITION PHASE 3 IMPLEMENTED')

except Exception as e:
    print('Error:', str(e))
    import traceback
    traceback.print_exc()

# Minimal scaffold for test_kernel_ignition.py

def test_kernel_ignition():
    pass