# Python Module Symbol Index

Generated: 2026-02-20T02:43:00.758979+00:00

- Modules scanned: 409
- Parse errors: 0
- Total functions: 1205
- Total classes: 438
- Total constants: 295
- Total explicit exports (__all__): 26

## Modules

### FIX_NEXUSMON_LAUNCHERS
- Path: FIX_NEXUSMON_LAUNCHERS.py
- Functions (4): _lan_ip, main, patch_typo, write_file
- Classes (0): -
- Constants (1): ROOT
- Exports (0): -

### HEALTHCHECK
- Path: HEALTHCHECK.py
- Functions (1): main
- Classes (1): HealthChecker
- Constants (0): -
- Exports (0): -

### ONE_BUTTON_NEXUSMON_OWNERSHIP_PACK
- Path: ONE_BUTTON_NEXUSMON_OWNERSHIP_PACK.py
- Functions (7): atomic_write_new, ensure_dir, main, now_utc_iso, prompt_default, rel, sanitize_single_line
- Classes (0): -
- Constants (1): ROOT
- Exports (0): -

### TOOLS_REPO_MAP
- Path: TOOLS_REPO_MAP.py
- Functions (6): get_tools_repo_map, is_excluded_dir, is_excluded_file, main, safe_relpath, sha1_file
- Classes (0): -
- Constants (6): EXCLUDE_DIRS, EXCLUDE_EXT, OUT_DIR, OUT_JSON, OUT_MD, ROOT
- Exports (0): -

### addons
- Path: addons/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.api
- Path: addons/api/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.api.addons_router
- Path: addons/api/addons_router.py
- Functions (43): backup_export, backup_import, backup_rollback, budget_get, budget_reset, budget_simulate, budget_spend, contract_get, contract_save, contract_seal, contract_validate, drift_get, drift_record, drift_scan, entropy_get, entropy_spend, golden_list, golden_record, golden_replay, ledger_declare, ledger_list, ledger_validate, memory_get, memory_list, memory_put, pack_download, pack_list, pack_store, pack_verify, patch_apply, patch_approve, patch_list, patch_rollback, patch_submit, quarantine_enter, quarantine_exit, quarantine_status, replay, strategy_check, strategy_kill, strategy_list, strategy_register, strategy_seal
- Classes (18): BudgetSimRequest, BudgetSpendRequest, ContractSealRequest, EntropySpendRequest, GoldenRecordRequest, GoldenReplayRequest, LeverRequest, MemoryGetRequest, MemoryPutRequest, PackStoreRequest, PatchActionRequest, PatchSubmitRequest, QuarantineEnterRequest, QuarantineExitRequest, StrategyCheckRequest, StrategyKillRequest, StrategyRegisterRequest, StrategySealRequest
- Constants (0): -
- Exports (0): -

### addons.api.dashboard_router
- Path: addons/api/dashboard_router.py
- Functions (3): dashboard, pwa_manifest, pwa_sw
- Classes (0): -
- Constants (3): _DASHBOARD_HTML, _MANIFEST, _SW_JS
- Exports (0): -

### addons.api.guardrails_router
- Path: addons/api/guardrails_router.py
- Functions (24): get_baselines, get_decay, get_falsification, get_interference, get_irreversibility, get_negative, get_pressure, get_regret, get_saturation, get_shadow, get_silence, get_stability, record_baseline, record_decay, record_interference, record_negative, record_pressure, record_regret, record_saturation, record_silence, shadow_replay, stability_check, submit_falsification, tag_irreversibility
- Classes (12): BaselineRequest, FalsificationRequest, InterferenceRequest, IrreversibilityRequest, NegativeZoneRequest, PressureRequest, RegretRequest, ReturnsRequest, ShadowReplayRequest, SilenceRequest, StabilityRequest, TemplateRunRequest
- Constants (0): -
- Exports (0): -

### addons.api.ui_router
- Path: addons/api/ui_router.py
- Functions (7): _get_core, api_audit, api_capabilities, api_execute, api_info, get_orchestrator, ui_page
- Classes (1): ExecuteRequest
- Constants (1): _UI_HTML
- Exports (0): -

### addons.approval_queue
- Path: addons/approval_queue.py
- Functions (8): _audit, _queue_path, _rewrite_queue, apply_patch, approve_patch, list_patches, rollback_patch, submit_patch
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.auth_gate
- Path: addons/auth_gate.py
- Functions (3): _append_audit, _client_ip, _is_localhost
- Classes (1): LANAuthMiddleware
- Constants (2): _LOCALHOST_ADDRS, _SAFE_METHODS
- Exports (0): -

### addons.backup
- Path: addons/backup.py
- Functions (4): _audit, export_backup, import_backup, rollback_import
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.budget
- Path: addons/budget.py
- Functions (8): _audit, _load, _save, get_budget, reserve, reset_budget, simulate_burn, spend
- Classes (0): -
- Constants (1): _BUDGET_FILE
- Exports (0): -

### addons.causal_ledger
- Path: addons/causal_ledger.py
- Functions (4): _audit, declare_lever, load_ledger, validate_lever
- Classes (0): -
- Constants (1): _LEDGER_FILE
- Exports (0): -

### addons.config_ext
- Path: addons/config_ext.py
- Functions (3): get_config, load_addon_config, reload_config
- Classes (0): -
- Constants (1): _ENV_PREFIX
- Exports (0): -

### addons.data
- Path: addons/data/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.drift_scanner
- Path: addons/drift_scanner.py
- Functions (5): _audit, _load_metric, compute_drift, record_metric, scan_all_metrics
- Classes (0): -
- Constants (1): _DRIFT_FILE
- Exports (0): -

### addons.encrypted_storage
- Path: addons/encrypted_storage.py
- Functions (10): _constant_time_eq, _derive_key, _hmac_sha256, _xor_bytes, decrypt_blob, encrypt_blob, get_encryption_key, is_encryption_enabled, load_encrypted_jsonl, save_encrypted_jsonl
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.entropy_budget
- Path: addons/entropy_budget.py
- Functions (7): _audit, _load, _maybe_reset, _save, _week_start, get_entropy_budget, spend_entropy
- Classes (0): -
- Constants (1): _ENTROPY_FILE
- Exports (0): -

### addons.golden_run
- Path: addons/golden_run.py
- Functions (6): _audit, _load_runs, _state_hash, list_golden_runs, record_golden_run, replay_and_verify
- Classes (0): -
- Constants (1): _GOLDEN_FILE
- Exports (0): -

### addons.guardrails
- Path: addons/guardrails.py
- Functions (31): _append_jsonl, _audit, _dir, _load_json, _load_jsonl, _save_json, compute_half_life, detect_saturation, get_baselines, get_coupling_graph, get_falsifications, get_irreversibility_tags, get_negative_zones, get_pressure_map, get_regret_log, get_shadow_replays, get_silence_signals, get_stability_checks, record_baseline, record_interference, record_negative_zone, record_pressure, record_regret, record_returns, record_silence, record_template_run, shadow_replay, should_avoid, stability_check, submit_falsification, tag_irreversibility
- Classes (0): -
- Constants (1): _GUARDRAILS_DIR
- Exports (0): -

### addons.memory_boundaries
- Path: addons/memory_boundaries.py
- Functions (9): _load_store, _memory_dir, _save_store, _store_path, delete, dump_store, get, list_keys, put
- Classes (0): -
- Constants (1): _STORES
- Exports (0): -

### addons.operator_contract
- Path: addons/operator_contract.py
- Functions (6): _audit, _contracts_dir, get_active_contract, save_contract, seal_contract, validate_action
- Classes (0): -
- Constants (1): _DEFAULT_CONTRACT
- Exports (0): -

### addons.pack_artifacts
- Path: addons/pack_artifacts.py
- Functions (6): _audit, _packs_dir, download_pack, list_packs, store_pack, verify_pack
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.quarantine
- Path: addons/quarantine.py
- Functions (7): _audit, _load_state, _save_state, enter_quarantine, exit_quarantine, get_quarantine_status, is_quarantined
- Classes (0): -
- Constants (1): _STATE_FILE
- Exports (0): -

### addons.rate_limiter
- Path: addons/rate_limiter.py
- Functions (0): -
- Classes (2): RateLimitMiddleware, _TokenBucket
- Constants (0): -
- Exports (0): -

### addons.red_team_tests
- Path: addons/red_team_tests.py
- Functions (1): run_red_team
- Classes (9): TestAdversarialInputStability, TestCausalLedgerEnforcement, TestConflictingAB, TestDuplicatedRuns, TestEncryptionTamper, TestEntropyOverCap, TestFakeROISpike, TestInvalidApprovals, TestStrategyKillSwitch
- Constants (0): -
- Exports (0): -

### addons.replay
- Path: addons/replay.py
- Functions (2): load_audit_entries, replay_state
- Classes (0): -
- Constants (0): -
- Exports (0): -

### addons.schema_version
- Path: addons/schema_version.py
- Functions (7): _append_audit, _backup_data, _migrate_v1, _read_version, _write_version, register_migration, run_migrations
- Classes (0): -
- Constants (1): CURRENT_SCHEMA_VERSION
- Exports (0): -

### addons.security
- Path: addons/security.py
- Functions (11): _jwt_algorithm, _jwt_secret, _security_log_path, append_security_event, create_access_token, decode_access_token, get_current_user, honeypot_endpoint, read_security_events, record_honeypot_hit, security_status_snapshot
- Classes (3): IDSMiddleware, RoleChecker, TokenData
- Constants (0): -
- Exports (0): -

### addons.strategy_registry
- Path: addons/strategy_registry.py
- Functions (8): _audit, _load, _save, check_kill_criteria, kill_strategy, list_strategies, register_strategy, seal_strategy
- Classes (0): -
- Constants (1): _REGISTRY_FILE
- Exports (0): -

### addons.swarm_protocol
- Path: addons/swarm_protocol.py
- Functions (0): -
- Classes (2): PacketBus, SwarmPacket
- Constants (0): -
- Exports (0): -

### api
- Path: api/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### backend.governor.audit
- Path: backend/governor/audit.py
- Functions (0): -
- Classes (1): Audit
- Constants (0): -
- Exports (0): -

### backend.governor.permissions
- Path: backend/governor/permissions.py
- Functions (0): -
- Classes (1): Permissions
- Constants (0): -
- Exports (0): -

### backend.patchpack.loader
- Path: backend/patchpack/loader.py
- Functions (0): -
- Classes (1): Loader
- Constants (0): -
- Exports (0): -

### backend.patchpack.validator
- Path: backend/patchpack/validator.py
- Functions (0): -
- Classes (1): Validator
- Constants (0): -
- Exports (0): -

### backend.runtime.api.meta_routes
- Path: backend/runtime/api/meta_routes.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### backend.runtime.api.server
- Path: backend/runtime/api/server.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### backend.runtime.core.autoloop
- Path: backend/runtime/core/autoloop.py
- Functions (0): -
- Classes (1): AutoLoop
- Constants (0): -
- Exports (0): -

### backend.runtime.core.engine
- Path: backend/runtime/core/engine.py
- Functions (0): -
- Classes (2): MissionEngine, SwarmEngine
- Constants (0): -
- Exports (0): -

### backend.runtime.core.telemetry
- Path: backend/runtime/core/telemetry.py
- Functions (0): -
- Classes (1): Telemetry
- Constants (0): -
- Exports (0): -

### backend.runtime.storage.db
- Path: backend/runtime/storage/db.py
- Functions (0): -
- Classes (1): Database
- Constants (0): -
- Exports (0): -

### bootstrap.ignite_runtime
- Path: bootstrap/ignite_runtime.py
- Functions (4): ensure_node_modules, main, run, shutdown
- Classes (0): -
- Constants (2): ROOT, UI_DIR
- Exports (0): -

### companion
- Path: companion.py
- Functions (1): main
- Classes (19): BuilderWorker, CommitEngine, CommitState, CompanionMode, EvolutionMechanism, ExecutionLog, IntelligenceLayer, Memory, ModeManager, OperatorMode, ScoutWorker, NexusmonCompanion, SystemMode, TaskContext, VerifyWorker, Worker, WorkerResult, WorkerSwarm, WorkerType
- Constants (0): -
- Exports (0): -

### companion_cli
- Path: companion_cli.py
- Functions (3): interactive_mode, main, print_mode_indicator
- Classes (0): -
- Constants (0): -
- Exports (0): -

### companion_examples
- Path: companion_examples.py
- Functions (10): example_basic_interaction, example_commit_states, example_custom_workers, example_evolution_mechanism, example_intelligence_learning, example_memory_persistence, example_usage, example_with_nexusmon_core, example_worker_swarm, main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### control_plane.decision_logger
- Path: control_plane/decision_logger.py
- Functions (0): -
- Classes (1): DecisionLogger
- Constants (2): _DATA_PATH, _DIR
- Exports (0): -

### control_plane.event_debouncer
- Path: control_plane/event_debouncer.py
- Functions (0): -
- Classes (1): EventDebouncer
- Constants (0): -
- Exports (0): -

### control_plane.expression_eval
- Path: control_plane/expression_eval.py
- Functions (1): evaluate
- Classes (0): -
- Constants (1): _OPS
- Exports (0): -

### control_plane.layer_weaver.decision_logger
- Path: control_plane/layer_weaver/decision_logger.py
- Functions (0): -
- Classes (1): DecisionLogger
- Constants (2): _DATA_PATH, _DIR
- Exports (0): -

### control_plane.layer_weaver.event_debouncer
- Path: control_plane/layer_weaver/event_debouncer.py
- Functions (0): -
- Classes (1): EventDebouncer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.expression_eval
- Path: control_plane/layer_weaver/expression_eval.py
- Functions (2): evaluate_comparison, safe_eval
- Classes (1): _SafeEval
- Constants (2): _BOOL_OPS, _COMPARE_OPS
- Exports (0): -

### control_plane.layer_weaver.layers
- Path: control_plane/layer_weaver/layers/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.base
- Path: control_plane/layer_weaver/layers/base.py
- Functions (0): -
- Classes (1): BaseLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.build
- Path: control_plane/layer_weaver/layers/build.py
- Functions (0): -
- Classes (1): BuildLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.health
- Path: control_plane/layer_weaver/layers/health.py
- Functions (0): -
- Classes (1): HealthLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.memory
- Path: control_plane/layer_weaver/layers/memory.py
- Functions (0): -
- Classes (1): MemoryLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.money
- Path: control_plane/layer_weaver/layers/money.py
- Functions (0): -
- Classes (1): MoneyLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.permissions
- Path: control_plane/layer_weaver/layers/permissions.py
- Functions (0): -
- Classes (1): PermissionsLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.layers.swarm_health
- Path: control_plane/layer_weaver/layers/swarm_health.py
- Functions (0): -
- Classes (1): SwarmHealthLayer
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.regime
- Path: control_plane/layer_weaver/regime.py
- Functions (0): -
- Classes (1): RegimeManager
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.scoring
- Path: control_plane/layer_weaver/scoring.py
- Functions (11): _clamp, _magnitude_value, _normalize_delta, check_constraints, check_guardrails, compute_benefit, compute_coupling_damage, compute_risk, compute_uncertainty, score_action, select_best_action
- Classes (0): -
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.state_store
- Path: control_plane/layer_weaver/state_store.py
- Functions (0): -
- Classes (1): StateStore
- Constants (3): _DATA_PATH, _DIR, _SCHEMA_PATH
- Exports (0): -

### control_plane.layer_weaver.nexusmon_adapter
- Path: control_plane/layer_weaver/nexusmon_adapter.py
- Functions (0): -
- Classes (2): InProcessNexusmonBus, NexusmonAdapter
- Constants (0): -
- Exports (0): -

### control_plane.layer_weaver.verification_runner
- Path: control_plane/layer_weaver/verification_runner.py
- Functions (3): _deadline_seconds, _load_actions, main
- Classes (1): VerificationRunner
- Constants (2): _ACTIONS_PATH, _DIR
- Exports (0): -

### control_plane.layer_weaver.verification_store
- Path: control_plane/layer_weaver/verification_store.py
- Functions (0): -
- Classes (1): VerificationStore
- Constants (2): _DATA_PATH, _DIR
- Exports (0): -

### control_plane.layer_weaver.weaver_service
- Path: control_plane/layer_weaver/weaver_service.py
- Functions (6): _file_hash, _load_json, _load_schema, compute_config_hash, main, validate_configs
- Classes (1): WeaverService
- Constants (6): _ACTIONS_PATH, _COUPLING_PATH, _DATA, _DIR, _OBJECTIVES_PATH, _SCHEMAS
- Exports (0): -

### control_plane.layers
- Path: control_plane/layers/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### control_plane.layers.base
- Path: control_plane/layers/base.py
- Functions (0): -
- Classes (1): BaseLayer
- Constants (0): -
- Exports (0): -

### control_plane.layers.build
- Path: control_plane/layers/build.py
- Functions (0): -
- Classes (1): BuildLayer
- Constants (0): -
- Exports (0): -

### control_plane.layers.health
- Path: control_plane/layers/health.py
- Functions (0): -
- Classes (1): HealthLayer
- Constants (0): -
- Exports (0): -

### control_plane.layers.memory
- Path: control_plane/layers/memory.py
- Functions (0): -
- Classes (1): MemoryLayer
- Constants (0): -
- Exports (0): -

### control_plane.layers.money
- Path: control_plane/layers/money.py
- Functions (0): -
- Classes (1): MoneyLayer
- Constants (0): -
- Exports (0): -

### control_plane.layers.permissions
- Path: control_plane/layers/permissions.py
- Functions (0): -
- Classes (1): PermissionsLayer
- Constants (0): -
- Exports (0): -

### control_plane.layers.swarm_health
- Path: control_plane/layers/swarm_health.py
- Functions (0): -
- Classes (1): SwarmHealthLayer
- Constants (0): -
- Exports (0): -

### control_plane.regime
- Path: control_plane/regime.py
- Functions (0): -
- Classes (2): RegimeManager, _RegimeState
- Constants (1): _DIR
- Exports (0): -

### control_plane.scoring
- Path: control_plane/scoring.py
- Functions (5): _benefit, _coupling_damage, _risk, score_action, select_best
- Classes (0): -
- Constants (2): _DIR, _NORM_SCALE
- Exports (0): -

### control_plane.state_store
- Path: control_plane/state_store.py
- Functions (0): -
- Classes (1): StateStore
- Constants (3): _DATA_PATH, _DIR, _SCHEMA_PATH
- Exports (0): -

### control_plane.nexusmon_adapter
- Path: control_plane/nexusmon_adapter.py
- Functions (0): -
- Classes (1): NexusmonAdapter
- Constants (0): -
- Exports (0): -

### control_plane.verification_runner
- Path: control_plane/verification_runner.py
- Functions (8): _hash_verify_spec, _make_dedupe_key, _now_iso, _now_utc, _read_state_records_from_offset, _sha256, _state_file_offset, main
- Classes (4): DeltaEvaluator, VerificationRunner, _InMemoryJobStore, _PgJobStore
- Constants (15): DEFAULT_LEASE_SECONDS, DEFAULT_MAX_ATTEMPTS, HEARTBEAT_INTERVAL_SECONDS, STATUS_CANCELLED, STATUS_DEADLETTERED, STATUS_EXPIRED, STATUS_FAILED, STATUS_PASSED, STATUS_QUEUED, STATUS_WAITING, _ACTIONS_PATH, _DIR, _PARENT, _STATE_JSONL, _TERMINAL
- Exports (0): -

### control_plane.verification_store
- Path: control_plane/verification_store.py
- Functions (0): -
- Classes (1): VerificationStore
- Constants (2): _DATA_PATH, _DIR
- Exports (0): -

### control_plane.weaver_service
- Path: control_plane/weaver_service.py
- Functions (3): _build_components, main, run_cycle
- Classes (0): -
- Constants (3): _ACTIONS_PATH, _DIR, _PARENT
- Exports (0): -

### core
- Path: core/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.activity_schema
- Path: core/activity_schema.py
- Functions (2): compute_event_id, validate_event
- Classes (0): -
- Constants (1): EVENT_SCHEMA_VERSION
- Exports (0): -

### core.activity_stream
- Path: core/activity_stream.py
- Functions (2): initialize_activity_stream, record_event
- Classes (0): -
- Constants (3): EVENTS_FILE, SESSION_FILE, SESSION_ID
- Exports (0): -

### core.ai_audit
- Path: core/ai_audit.py
- Functions (7): _append, _next_seq, _tail, log_decision, log_model_call, tail_ai, tail_decisions
- Classes (0): -
- Constants (4): AI_AUDIT_FILE, DATA_DIR, DECISION_AUDIT_FILE, ROOT
- Exports (0): -

### core.anomaly_detector
- Path: core/anomaly_detector.py
- Functions (1): detect_anomalies
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.atomic
- Path: core/atomic.py
- Functions (2): atomic_append_jsonl, atomic_write_json
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.awareness_api
- Path: core/awareness_api.py
- Functions (2): _audit, register_awareness_api
- Classes (0): -
- Constants (3): AWARENESS_LOG, DATA_DIR, ROOT
- Exports (0): -

### core.awareness_model
- Path: core/awareness_model.py
- Functions (9): _audit, _load_audit_events, _load_missions, _risk_from_status, _safe_iso, build_topology, compute_alerts, normalize_events, self_check
- Classes (1): NormalizedEvent
- Constants (6): AUDIT_FILE, AWARENESS_LOG, DATA_DIR, EVENT_FIELDS, MISSIONS_FILE, ROOT
- Exports (0): -

### core.bypass_map
- Path: core/bypass_map.py
- Functions (1): build_bypass_map
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.cold_start
- Path: core/cold_start.py
- Functions (12): _ensure_dirs, _ensure_json_files, _ensure_jsonl_files, _ensure_system_identity, _ensure_text_files, _machine_fingerprint, _now, _safe_mkdir, _safe_touch_jsonl, _safe_touch_text, _safe_write_json, ensure_cold_start
- Classes (0): -
- Constants (2): DATA_DIR, ROOT
- Exports (0): -

### core.companion
- Path: core/companion.py
- Functions (13): _audit_companion, _audit_model_call, _build_context_block, _companion_config, _load_config, _load_system_prompt, _memory_path, _rule_engine, chat, load_memory, record_mission_outcome, save_memory, update_summary
- Classes (0): -
- Constants (6): AUDIT_FILE, CONFIG_FILE, DATA_DIR, MAX_OUTCOMES, PROMPT_DIR, ROOT
- Exports (0): -

### core.companion_master
- Path: core/companion_master.py
- Functions (8): _load_master, _save_master, ensure_master, get_composite_context, record_epoch, record_insight, record_mission_observed, self_assessment
- Classes (0): -
- Constants (3): DATA_DIR, MASTER_FILE, ROOT
- Exports (0): -

### core.config_loader
- Path: core/config_loader.py
- Functions (6): _invalidate, companion, get, is_offline, load, models
- Classes (0): -
- Constants (2): CONFIG_FILE, ROOT
- Exports (0): -

### core.context_pack
- Path: core/context_pack.py
- Functions (6): _hash, after_mission, before_mission, daily_tick, get_scoreboard, load
- Classes (0): -
- Constants (2): DATA_DIR, ROOT
- Exports (0): -

### core.conversation_engine
- Path: core/conversation_engine.py
- Functions (1): get_conversation_engine
- Classes (3): ConversationEngine, IntentClassifier, ModeSelector
- Constants (0): -
- Exports (0): -

### core.counterfactual_engine
- Path: core/counterfactual_engine.py
- Functions (0): -
- Classes (1): CounterfactualEngine
- Constants (0): -
- Exports (0): -

### core.daily_coach
- Path: core/daily_coach.py
- Functions (0): -
- Classes (1): DailyCoach
- Constants (0): -
- Exports (0): -

### core.divergence_engine
- Path: core/divergence_engine.py
- Functions (0): -
- Classes (1): DivergenceEngine
- Constants (0): -
- Exports (0): -

### core.enforcement_mode
- Path: core/enforcement_mode.py
- Functions (4): get_mode, handle_violation, load_config, should_enforce
- Classes (0): -
- Constants (1): CONFIG_PATH
- Exports (0): -

### core.entropy_monitor
- Path: core/entropy_monitor.py
- Functions (0): -
- Classes (1): EntropyMonitor
- Constants (0): -
- Exports (0): -

### core.evidence_pack
- Path: core/evidence_pack.py
- Functions (1): create_evidence_pack
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.evolution_memory
- Path: core/evolution_memory.py
- Functions (0): -
- Classes (1): EvolutionMemory
- Constants (0): -
- Exports (0): -

### core.extension_registry
- Path: core/extension_registry.py
- Functions (0): -
- Classes (1): ExtensionRegistry
- Constants (0): -
- Exports (0): -

### core.forensics
- Path: core/forensics.py
- Functions (12): _audit, _find_mission, _load_artifacts, _load_audit, _load_missions, _summarize_changes, _summarize_contributing_factors, _summarize_preceding_actions, _summarize_what_happened, build_casefile, build_timeline, self_check
- Classes (2): CaseFile, TimelineEvent
- Constants (6): AUDIT_FILE, DATA_DIR, FORENSICS_LOG, MISSIONS_FILE, PACKS_DIR, ROOT
- Exports (0): -

### core.forensics_api
- Path: core/forensics_api.py
- Functions (3): _audit, _index_missions_with_activity, register_forensics_api
- Classes (0): -
- Constants (4): DATA_DIR, FORENSICS_LOG, MISSIONS_FILE, ROOT
- Exports (0): -

### core.fs_observer
- Path: core/fs_observer.py
- Functions (2): observed_read, observed_write
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.hologram
- Path: core/hologram.py
- Functions (28): _append_drift_event, _build_delta_graph, _build_stability_field, _build_trajectory, _burst_enabled, _drift_event_count, _get_drift_indicators, _load_state, _max_same_context_tag, _metrics_per_metric_count, _powers_for_level, _read_drift_events, _save_state, _verdict_badge, _verified_trials, _why_failed_hint, compute_effects, compute_level, compute_power_currencies, compute_xp, create_burst_batch, detect_drift, hologram_trial_detail, kill_burst_batch, list_burst_batches, suggest_best_followups, suggest_drift_correction, toggle_burst_mode
- Classes (0): -
- Constants (6): LEVELS, _BURST_FILE, _DRIFT_EVENTS_FILE, _HOLO_DIR, _LOCK, _STATE_FILE
- Exports (0): -

### core.hologram_api
- Path: core/hologram_api.py
- Functions (1): register_hologram_api
- Classes (5): BurstBatchRequest, BurstBatchTrialSpec, BurstToggleRequest, DriftCheckRequest, SuggestionRequest
- Constants (0): -
- Exports (0): -

### core.intent_detector
- Path: core/intent_detector.py
- Functions (0): -
- Classes (1): IntentDetector
- Constants (0): -
- Exports (0): -

### core.kill_switch
- Path: core/kill_switch.py
- Functions (2): activate_kill_switch, safe_halt
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.knowledge_graph
- Path: core/knowledge_graph.py
- Functions (0): -
- Classes (1): KnowledgeGraph
- Constants (0): -
- Exports (0): -

### core.license_guard
- Path: core/license_guard.py
- Functions (2): enforce, verify_repository
- Classes (0): -
- Constants (1): AUTH_URL
- Exports (0): -

### core.log_retention
- Path: core/log_retention.py
- Functions (2): prune_logs, rotate_logs
- Classes (0): -
- Constants (1): RETENTION_CONFIG
- Exports (0): -

### core.macro_builder
- Path: core/macro_builder.py
- Functions (1): build_macros
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.market_lab
- Path: core/market_lab.py
- Functions (2): backtest_strategy, self_check
- Classes (0): -
- Constants (2): DATA_DIR, MARKET_LOG
- Exports (0): -

### core.market_lab_api
- Path: core/market_lab_api.py
- Functions (1): register_market_lab_api
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.memory_engine
- Path: core/memory_engine.py
- Functions (1): get_memory_engine
- Classes (1): MemoryEngine
- Constants (0): -
- Exports (0): -

### core.mission_solver
- Path: core/mission_solver.py
- Functions (4): _load_solver_prompt, _offline_stub, _write_plan, solve
- Classes (0): -
- Constants (4): AUDIT_FILE, PREPARED_DIR, PROMPT_DIR, ROOT
- Exports (0): -

### core.model_router
- Path: core/model_router.py
- Functions (11): _call_anthropic, _call_openai, _err_response, _get_api_key, _load_config, _ok_response, call, get_model_config, get_status, is_offline, record_call
- Classes (0): -
- Constants (2): CONFIG_FILE, ROOT
- Exports (0): -

### core.new_module
- Path: core/new_module.py
- Functions (1): new_functionality
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.next_move
- Path: core/next_move.py
- Functions (2): predict_next_action, summarize_recent_activity
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.nexusmon_models
- Path: core/nexusmon_models.py
- Functions (0): -
- Classes (20): AuditEvent, ChatContext, ChatModeType, ChatReply, ChatRequest, ConversationContext, ConversationTurn, Mission, MissionDraft, NexusForm, NexusFormType, OperatorMemory, OperatorProfile, Persona, PersonaConstraints, PersonaStyle, StateSnapshot, SuggestedAction, SuggestedActionType, SystemHealth
- Constants (0): -
- Exports (0): -

### core.nexusmon_router
- Path: core/nexusmon_router.py
- Functions (13): _emit_audit_event, _ensure_nexus_form, _ensure_operator_profile, _get_active_missions, _get_system_health, chat, get_conversation_history, get_operator_memory, get_operator_nexus_form, get_operator_profile, get_system_health, nexusmon_health, update_operator_memory
- Classes (0): -
- Constants (5): AUDIT_FILE, DATA_DIR, MISSIONS_FILE, NEXUS_FORMS_FILE, OPERATOR_PROFILES_FILE
- Exports (0): -

### core.normalizer
- Path: core/normalizer.py
- Functions (4): normalize_command, normalize_event, normalize_file_path, stable_hash
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.one_throat_wrapper
- Path: core/one_throat_wrapper.py
- Functions (1): one_throat_handler
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.operator_anchor
- Path: core/operator_anchor.py
- Functions (8): _generate_keys, _safe_run, compute_machine_fingerprint, compute_record_hash, load_or_create_anchor, sign_record, verify_fingerprint, verify_signature
- Classes (0): -
- Constants (1): ANCHOR_FILENAME
- Exports (0): -

### core.perf_ledger
- Path: core/perf_ledger.py
- Functions (0): -
- Classes (1): PerfLedger
- Constants (0): -
- Exports (0): -

### core.persona_engine
- Path: core/persona_engine.py
- Functions (2): get_persona, get_system_prompt
- Classes (1): PersonaEngine
- Constants (0): -
- Exports (0): -

### core.phase_engine
- Path: core/phase_engine.py
- Functions (0): -
- Classes (1): PhaseEngine
- Constants (0): -
- Exports (0): -

### core.process_observer
- Path: core/process_observer.py
- Functions (4): observe_process_end, observe_process_exception, observe_process_start, wrap_process_execution
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.reality_classifier
- Path: core/reality_classifier.py
- Functions (3): classify_action, handle_action, load_classifier_config
- Classes (0): -
- Constants (1): CONFIG_PATH
- Exports (0): -

### core.reality_firewall
- Path: core/reality_firewall.py
- Functions (3): classify_action, record_firewall_event, should_block
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.redaction
- Path: core/redaction.py
- Functions (1): redact_event
- Classes (0): -
- Constants (1): REDACTION_RULES
- Exports (0): -

### core.relevance_engine
- Path: core/relevance_engine.py
- Functions (0): -
- Classes (1): RelevanceEngine
- Constants (1): USEFULNESS_DECAY
- Exports (0): -

### core.replay_simulator
- Path: core/replay_simulator.py
- Functions (1): generate_replay_plan
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.safe_execution
- Path: core/safe_execution.py
- Functions (5): _ensure_dirs, count_pending, list_pending, mark_executed, prepare_action
- Classes (0): -
- Constants (3): CATEGORIES, PREPARED_DIR, ROOT
- Exports (0): -

### core.schema_guard
- Path: core/schema_guard.py
- Functions (1): validate
- Classes (0): -
- Constants (6): COMPANION_MEMORY_SCHEMA, EVOLUTION_RECORD_SCHEMA, MISSION_SCHEMA, PERF_RECORD_SCHEMA, PHASE_HISTORY_SCHEMA, _TYPE_MAP
- Exports (0): -

### core.sequence_miner
- Path: core/sequence_miner.py
- Functions (0): -
- Classes (1): SequenceMiner
- Constants (0): -
- Exports (0): -

### core.session_timer
- Path: core/session_timer.py
- Functions (0): -
- Classes (1): SessionTimer
- Constants (0): -
- Exports (0): -

### core.shell_api
- Path: core/shell_api.py
- Functions (1): register_shell_api
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.shell_registry
- Path: core/shell_registry.py
- Functions (3): list_modules, register_module, self_check
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.task_classifier
- Path: core/task_classifier.py
- Functions (0): -
- Classes (1): TaskClassifier
- Constants (0): -
- Exports (0): -

### core.time_source
- Path: core/time_source.py
- Functions (3): mission_timestamp, now, today
- Classes (0): -
- Constants (0): -
- Exports (0): -

### core.tool_gate
- Path: core/tool_gate.py
- Functions (3): _resolve_category, gate, is_allowed
- Classes (0): -
- Constants (1): _CATEGORY_MAP
- Exports (0): -

### core.trajectory_engine
- Path: core/trajectory_engine.py
- Functions (0): -
- Classes (1): TrajectoryEngine
- Constants (1): DEFAULT_FUTURE_STATE
- Exports (0): -

### core.trials
- Path: core/trials.py
- Functions (32): _append_jsonl, _append_trial, _audit_event, _builtin_resolve, _now_iso, _now_ts, _read_jsonl, _resolve_activation_rate, _resolve_conversion_rate, _resolve_cost_per_day, _resolve_errors_per_1k, _resolve_latency_p95, _resolve_retention_d1, add_note, compute_survival_scores, create_followup, get_audit_trail, get_survival_leaderboard, get_trial, inbox_completed, inbox_counts, inbox_needs_review, inbox_pending, list_available_metrics, load_all_trials, new_trial, rank_suggestions, register_metric, require_trial, resolve_metric, revert_trial, update_trial
- Classes (1): TrialGateError
- Constants (5): _AUDIT_FILE, _DATA_DIR, _LOCK, _SCORES_FILE, _TRIALS_FILE
- Exports (0): -

### core.trials_api
- Path: core/trials_api.py
- Functions (1): register_trials_api
- Classes (4): AddNoteRequest, CreateTrialRequest, FollowupRequest, NonTrialRequest
- Constants (0): -
- Exports (0): -

### core.trials_worker
- Path: core/trials_worker.py
- Functions (7): _parse_iso, _worker_loop, check_due_trials, evaluate_trial, start_worker, stop_worker, worker_status
- Classes (0): -
- Constants (2): _CHECK_INTERVAL_SEC, _WORKER_RUNNING
- Exports (0): -

### core.value_scoreboard
- Path: core/value_scoreboard.py
- Functions (3): get_top_metrics, load_scoreboard, update_scoreboard
- Classes (0): -
- Constants (1): SCOREBOARD_PATH
- Exports (0): -

### core.weekly_coach
- Path: core/weekly_coach.py
- Functions (0): -
- Classes (1): WeeklyCoach
- Constants (0): -
- Exports (0): -

### core.workflow_forecaster
- Path: core/workflow_forecaster.py
- Functions (0): -
- Classes (1): WorkflowForecaster
- Constants (0): -
- Exports (0): -

### core.world_model
- Path: core/world_model.py
- Functions (0): -
- Classes (1): WorldModel
- Constants (0): -
- Exports (0): -

### core.zapier_bridge
- Path: core/zapier_bridge.py
- Functions (7): _append_log, _check_secret, _load_zapier_config, _prune_dedupe, _write_audit, _write_mission, register_zapier_bridge
- Classes (2): ZapierEmitBody, ZapierInboundBody
- Constants (8): _AUDIT_FILE, _CONFIG_PATH, _DEDUPE_TTL, _INBOUND_LOG, _MISSIONS_FILE, _OUTBOUND_LOG, _ROOT, _ZAPIER_DIR
- Exports (0): -

### design
- Path: design/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### dev
- Path: dev/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### dev.decision_space_demo
- Path: dev/decision_space_demo.py
- Functions (2): _get, main
- Classes (0): -
- Constants (1): BASE_URL
- Exports (0): -

### dev.infra_simulation_demo
- Path: dev/infra_simulation_demo.py
- Functions (4): _get, _post, _print, main
- Classes (0): -
- Constants (1): BASE_URL
- Exports (0): -

### dev.network_sim_demo
- Path: dev/network_sim_demo.py
- Functions (4): _get, _post, main, send_sample
- Classes (0): -
- Constants (2): BASE_URL, NODES
- Exports (0): -

### docs
- Path: docs/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### evaluation
- Path: evaluation.py
- Functions (1): evaluate
- Classes (0): -
- Constants (0): -
- Exports (0): -

### examples
- Path: examples.py
- Functions (8): example_basic_tasks, example_code_execution, example_custom_plugin, example_do_anything, example_operator_sovereignty, example_plugin_system, main, show_examples
- Classes (0): -
- Constants (0): -
- Exports (0): -

### galileo
- Path: galileo/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (17): apply_gates, check_similarity, compute_jaccard, generate_ids, get_critic_prompt, get_experimentalist_prompt, get_generator_prompt, get_scorer_prompt, init_storage, inputs_hash, load_experiments, load_hypotheses, load_runs, save_run_record, score_hypothesis, should_accept, stableStringify

### galileo.determinism
- Path: galileo/determinism.py
- Functions (4): generate_ids, hash_sha256, inputs_hash, stableStringify
- Classes (0): -
- Constants (0): -
- Exports (0): -

### galileo.gates
- Path: galileo/gates.py
- Functions (6): apply_gates, gate_g0_falsifiable, gate_g1_specific, gate_g2_testable_locally, gate_g3_non_trivial, gate_g4_novelty
- Classes (0): -
- Constants (1): TAUTOLOGY_PATTERNS
- Exports (0): -

### galileo.prompts
- Path: galileo/prompts.py
- Functions (4): get_critic_prompt, get_experimentalist_prompt, get_generator_prompt, get_scorer_prompt
- Classes (0): -
- Constants (0): -
- Exports (0): -

### galileo.run
- Path: galileo/run.py
- Functions (5): _critique_hypothesis, _generate_hypotheses, _specify_experiment, _synthetic_hypotheses, run_galileo
- Classes (0): -
- Constants (0): -
- Exports (0): -

### galileo.scorer
- Path: galileo/scorer.py
- Functions (8): score_falsifiability, score_hypothesis, score_mechanistic_coherence, score_novelty, score_reproducibility, score_risk, score_test_cost, should_accept
- Classes (0): -
- Constants (0): -
- Exports (0): -

### galileo.similarity
- Path: galileo/similarity.py
- Functions (4): check_similarity, compute_jaccard, get_3grams, normalize_claim
- Classes (0): -
- Constants (0): -
- Exports (0): -

### galileo.storage
- Path: galileo/storage.py
- Functions (12): init_storage, load_domain_pack, load_experiments, load_hypotheses, load_priors, load_runs, read_jsonl, save_experiment, save_hypothesis, save_run_record, save_score, write_jsonl
- Classes (0): -
- Constants (1): GALILEO_DATA_DIR
- Exports (0): -

### jsonl_utils
- Path: jsonl_utils.py
- Functions (3): append_jsonl, read_jsonl, write_jsonl
- Classes (0): -
- Constants (0): -
- Exports (3): append_jsonl, read_jsonl, write_jsonl

### kernel_runtime
- Path: kernel_runtime/__init__.py
- Functions (1): initialize
- Classes (1): KernelRuntime
- Constants (0): -
- Exports (0): -

### kernel_runtime.orchestrator
- Path: kernel_runtime/orchestrator.py
- Functions (0): -
- Classes (1): NexusmonOrchestrator
- Constants (0): -
- Exports (0): -

### mobile.nexusmon_client
- Path: mobile/nexusmon_client.py
- Functions (1): send_request
- Classes (0): -
- Constants (1): SERVER_URL
- Exports (0): -

### models.ignition
- Path: models/ignition.py
- Functions (0): -
- Classes (1): IgnitionStateRequest
- Constants (0): -
- Exports (0): -

### models.lattice
- Path: models/lattice.py
- Functions (0): -
- Classes (1): LatticeStatusRequest
- Constants (0): -
- Exports (0): -

### models.sovereign
- Path: models/sovereign.py
- Functions (0): -
- Classes (1): SovereignDecisionRequest
- Constants (0): -
- Exports (0): -

### operator_console
- Path: operator_console/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### packs
- Path: packs/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### plugins
- Path: plugins/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### plugins.dataprocessing
- Path: plugins/dataprocessing.py
- Functions (1): register
- Classes (0): -
- Constants (0): -
- Exports (0): -

### plugins.filesystem
- Path: plugins/filesystem.py
- Functions (1): register
- Classes (0): -
- Constants (0): -
- Exports (0): -

### plugins.lead_audit
- Path: plugins/lead_audit.py
- Functions (7): audit_leads, calculate_engagement_score, calculate_recency_score, calculate_value_score, parse_csv_data, register, score_lead
- Classes (0): -
- Constants (0): -
- Exports (0): -

### plugins.mission_contract
- Path: plugins/mission_contract.py
- Functions (3): check_law_compliance, register, validate_mission_contract
- Classes (0): -
- Constants (2): REQUIRED_TOP_LEVEL_FIELDS, TWELVE_LAWS
- Exports (0): -

### plugins.reality_gate
- Path: plugins/reality_gate.py
- Functions (3): reality_gate, register, validate_learning_source
- Classes (0): -
- Constants (1): VALID_EXTERNAL_SIGNALS
- Exports (0): -

### prepared_actions
- Path: prepared_actions/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### run_server
- Path: run_server.py
- Functions (4): _lan_ip, _load_runtime_config, _resolve_host_port, main
- Classes (0): -
- Constants (2): ROOT, RUNTIME_CONFIG
- Exports (0): -

### run_nexusmon
- Path: run_nexusmon.py
- Functions (2): _lan_ip, run_tool
- Classes (0): -
- Constants (0): -
- Exports (0): -

### scripts.init_db
- Path: scripts/init_db.py
- Functions (1): init_database
- Classes (0): -
- Constants (0): -
- Exports (0): -

### self_check
- Path: self_check.py
- Functions (3): _expect_error, check, main
- Classes (0): -
- Constants (2): CHECKS_FAILED, CHECKS_PASSED
- Exports (0): -

### server
- Path: server.py
- Functions (18): _append_jsonl, _expected_operator_key, _get_operator_key, _read_state, _write_state, ai_status, build_dispatch, companion_history, companion_state_endpoint, get_mode, health, prepared_pending, runtime_scoreboard, set_mode, sovereign_dispatch, start_server, swarm_status, system_log
- Classes (3): BuildDispatchRequest, DispatchRequest, ModeRequest
- Constants (5): AUDIT_FILE, DATA_DIR, HEARTBEAT_FILE, MISSIONS_FILE, STATE_FILE
- Exports (1): app

### setup_theorem_kb
- Path: setup_theorem_kb.py
- Functions (4): main, parse_theorems, setup_kb, write_category_file
- Classes (0): -
- Constants (8): CATEGORIES_DIR, INDEX_FILE, KB_DIR, PARSED_FILE, RAW_FILE, RAW_THEOREMS, ROOT, THEOREM_RE
- Exports (0): -

### showcase
- Path: showcase.py
- Functions (3): main, print_header, print_success
- Classes (0): -
- Constants (0): -
- Exports (0): -

### src.main
- Path: src/main.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### src.patchpack
- Path: src/patchpack/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### src.patchpack.engine
- Path: src/patchpack/engine.py
- Functions (0): -
- Classes (1): PatchpackEngine
- Constants (1): PATCHPACK_DIR
- Exports (0): -

### src.patchpack.router
- Path: src/patchpack/router.py
- Functions (3): create_patch, list_patches, load_patch
- Classes (0): -
- Constants (0): -
- Exports (0): -

### swarm_runner
- Path: swarm_runner.py
- Functions (11): _audit, _process_one, _rewrite_missions, _worker_ai_solve, _worker_galileo_run, _worker_smoke, _worker_test_mission, _worker_unknown, _write_heartbeat, run_loop, run_swarm
- Classes (0): -
- Constants (8): AI_ELIGIBLE_CATEGORIES, AUDIT_FILE, DATA_DIR, HEARTBEAT_FILE, MISSIONS_FILE, PACKS_DIR, TICK_INTERVAL, WORKERS
- Exports (0): -

### nexusmon
- Path: nexusmon.py
- Functions (1): main
- Classes (3): OperatorSovereignty, NexusmonCore, TaskExecutor
- Constants (0): -
- Exports (0): -

### nexusmon
- Path: nexusmon/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (3): OperatorSovereignty, NexusmonCore, TaskExecutor

### nexusmon.backend
- Path: nexusmon/backend/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core
- Path: nexusmon/backend/core/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.avatar
- Path: nexusmon/backend/core/avatar_legacy/avatar.py
- Functions (0): -
- Classes (3): AvatarBrain, AvatarPresence, AvatarState
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.brain
- Path: nexusmon/backend/core/avatar_legacy/brain.py
- Functions (0): -
- Classes (1): AvatarBrain
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.controller
- Path: nexusmon/backend/core/avatar_legacy/controller.py
- Functions (0): -
- Classes (1): AvatarController
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.models
- Path: nexusmon/backend/core/avatar_legacy/models.py
- Functions (0): -
- Classes (1): Avatar
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.presence
- Path: nexusmon/backend/core/avatar_legacy/presence.py
- Functions (0): -
- Classes (1): AvatarPresence
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.renderer
- Path: nexusmon/backend/core/avatar_legacy/renderer.py
- Functions (0): -
- Classes (1): AvatarRenderer
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.avatar_legacy.state
- Path: nexusmon/backend/core/avatar_legacy/state.py
- Functions (0): -
- Classes (1): AvatarState
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cockpit.controller
- Path: nexusmon/backend/core/cockpit/controller.py
- Functions (0): -
- Classes (1): CockpitController
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cockpit.dashboard
- Path: nexusmon/backend/core/cockpit/dashboard.py
- Functions (0): -
- Classes (1): CockpitDashboard
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cockpit.models
- Path: nexusmon/backend/core/cockpit/models.py
- Functions (0): -
- Classes (1): Cockpit
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cosmology
- Path: nexusmon/backend/core/cosmology/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cosmology.link
- Path: nexusmon/backend/core/cosmology/link.py
- Functions (0): -
- Classes (1): Link
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cosmology.mesh
- Path: nexusmon/backend/core/cosmology/mesh.py
- Functions (0): -
- Classes (3): Link, MeshRouter, Node
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cosmology.mesh_router
- Path: nexusmon/backend/core/cosmology/mesh_router.py
- Functions (0): -
- Classes (1): MeshRouter
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.cosmology.node
- Path: nexusmon/backend/core/cosmology/node.py
- Functions (0): -
- Classes (1): Node
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.governor.governor
- Path: nexusmon/backend/core/governor/governor.py
- Functions (0): -
- Classes (1): Governor
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.mission.executor
- Path: nexusmon/backend/core/mission/executor.py
- Functions (0): -
- Classes (1): MissionExecutor
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.mission.mission
- Path: nexusmon/backend/core/mission/mission.py
- Functions (0): -
- Classes (4): MissionExecutor, MissionParser, MissionPlanner, MissionReporter
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.mission.models
- Path: nexusmon/backend/core/mission/models.py
- Functions (0): -
- Classes (2): Mission, Models
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.mission.parser
- Path: nexusmon/backend/core/mission/parser.py
- Functions (0): -
- Classes (2): MissionParser, Parser
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.mission.planner
- Path: nexusmon/backend/core/mission/planner.py
- Functions (0): -
- Classes (2): MissionPlanner, Planner
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.mission.reporter
- Path: nexusmon/backend/core/mission/reporter.py
- Functions (0): -
- Classes (1): MissionReporter
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.patchpack.patchpack
- Path: nexusmon/backend/core/patchpack/patchpack.py
- Functions (0): -
- Classes (1): Patchpack
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.session.session
- Path: nexusmon/backend/core/session/session.py
- Functions (0): -
- Classes (1): Session
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.behavior
- Path: nexusmon/backend/core/swarm/behavior.py
- Functions (0): -
- Classes (1): BehaviorEngine
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.formation
- Path: nexusmon/backend/core/swarm/formation.py
- Functions (0): -
- Classes (1): FormationEngine
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.manager
- Path: nexusmon/backend/core/swarm/manager.py
- Functions (0): -
- Classes (1): SwarmManager
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.models
- Path: nexusmon/backend/core/swarm/models.py
- Functions (0): -
- Classes (1): SwarmTask
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.monitor
- Path: nexusmon/backend/core/swarm/monitor.py
- Functions (0): -
- Classes (1): SwarmMonitor
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.registry
- Path: nexusmon/backend/core/swarm/registry.py
- Functions (0): -
- Classes (1): UnitRegistry
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.swarm
- Path: nexusmon/backend/core/swarm/swarm.py
- Functions (0): -
- Classes (4): BehaviorEngine, FormationEngine, Unit, UnitRegistry
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.unit
- Path: nexusmon/backend/core/swarm/unit.py
- Functions (0): -
- Classes (1): Unit
- Constants (0): -
- Exports (0): -

### nexusmon.backend.core.swarm.worker
- Path: nexusmon/backend/core/swarm/worker.py
- Functions (0): -
- Classes (1): SwarmWorker
- Constants (0): -
- Exports (0): -

### nexusmon.backend.runtime.bootstrap
- Path: nexusmon/backend/runtime/bootstrap.py
- Functions (1): bootstrap
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.backend.runtime.engine
- Path: nexusmon/backend/runtime/engine.py
- Functions (0): -
- Classes (1): Engine
- Constants (0): -
- Exports (0): -

### nexusmon.runtime
- Path: nexusmon/runtime/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.runtime.ignition
- Path: nexusmon/runtime/ignition.py
- Functions (4): build_default_ignition, step_load_kernels, step_load_missions, step_load_patchpacks
- Classes (3): IgnitionEvent, RuntimeIgnition, RuntimeIgnitionState
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.layout
- Path: nexusmon/ui/cockpit/layout/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels
- Path: nexusmon/ui/cockpit/panels.py
- Functions (0): -
- Classes (6): AvatarPanel, CosmologyPanel, MissionsPanel, PatchpackPanel, SwarmPanel, SystemPanel
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels.avatar
- Path: nexusmon/ui/cockpit/panels/avatar/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels.cosmology
- Path: nexusmon/ui/cockpit/panels/cosmology/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels.missions
- Path: nexusmon/ui/cockpit/panels/missions/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels.patchpack
- Path: nexusmon/ui/cockpit/panels/patchpack/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels.swarm
- Path: nexusmon/ui/cockpit/panels/swarm/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.panels.system
- Path: nexusmon/ui/cockpit/panels/system/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon.ui.cockpit.state
- Path: nexusmon/ui/cockpit/state/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_app.api.hologram
- Path: nexusmon_app/api/hologram.py
- Functions (1): hologram
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_app.core.hologram_presence
- Path: nexusmon_app/core/hologram_presence.py
- Functions (8): get_current_phase, get_entropy_level, get_hologram_payload, get_hologram_state, get_last_mission_summary, get_operator_binding_status, get_personality_vector, get_trajectory_info
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_cli
- Path: nexusmon_cli.py
- Functions (1): cli_main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime
- Path: nexusmon_runtime/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api
- Path: nexusmon_runtime/api/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.admin
- Path: nexusmon_runtime/api/admin.py
- Functions (4): check_operator_sovereignty, execute_operator_command, get_sovereignty_status, schedule_maintenance
- Classes (2): OperatorCommand, SovereigntyCheck
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.arena
- Path: nexusmon_runtime/api/arena.py
- Functions (5): arena_self_check, get_arena_config, get_arena_run, list_arena_runs, start_arena_run
- Classes (1): ArenaRunRequest
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.companion_state
- Path: nexusmon_runtime/api/companion_state.py
- Functions (1): companion_state
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.debug
- Path: nexusmon_runtime/api/debug.py
- Functions (1): storage_check
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.ecosystem
- Path: nexusmon_runtime/api/ecosystem.py
- Functions (8): _get_loop, auto_start, auto_stop, ecosystem_run, ecosystem_status, ecosystem_verify, get_pack, set_engine_provider
- Classes (2): AutoStartRequest, EcosystemRunRequest
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.factory_routes
- Path: nexusmon_runtime/api/factory_routes.py
- Functions (6): decisions_latest, execute_artifact, factory_graph, factory_intake, factory_mission, factory_missions
- Classes (1): ArtifactExecutionRequest
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.galileo_routes
- Path: nexusmon_runtime/api/galileo_routes.py
- Functions (4): galileo_experiments, galileo_hypotheses, galileo_run, galileo_run_get
- Classes (1): GalileoRunBody
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.galileo_storage_shim
- Path: nexusmon_runtime/api/galileo_storage_shim.py
- Functions (4): _read_jsonl, read_experiments, read_hypotheses, read_runs
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.infra
- Path: nexusmon_runtime/api/infra.py
- Functions (8): _infra_enabled, infra_autoscale_plan, infra_backup_plan, infra_events, infra_overview, infra_plan_missions, infra_state, ingest_metrics
- Classes (1): InfraMetricSample
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.meta_routes
- Path: nexusmon_runtime/api/meta_routes.py
- Functions (13): apply_sovereign_control, create_mission, execute_kernel_ignition, get_cosmology, get_ignition_status, get_lattice_status, get_missions, get_patchpack, get_sovereign_status, get_swarm, get_system, make_sovereign_decision, process_task_matrix
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.missions
- Path: nexusmon_runtime/api/missions.py
- Functions (4): approve_mission, create_mission, list_missions, run_mission
- Classes (3): ApproveMissionRequest, CreateMissionRequest, RunMissionRequest
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.observability
- Path: nexusmon_runtime/api/observability.py
- Functions (2): health, ready
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.perf_routes
- Path: nexusmon_runtime/api/perf_routes.py
- Functions (3): _require_operator, perf_bench, perf_snapshot
- Classes (0): -
- Constants (2): DATA_DIR, PERF_DIR
- Exports (0): -

### nexusmon_runtime.api.runtime_endpoints
- Path: nexusmon_runtime/api/runtime_endpoints.py
- Functions (1): runtime_scoreboard
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.server
- Path: nexusmon_runtime/api/server.py
- Functions (38): _append_jsonl, _file_in_ui, _lan_ip, _load_operator_pin, _load_runtime_config, _resolve_offline_mode, _tail_jsonl, ai_status, app_js_file, app_js_head, audit_tail, build_orchestrator, companion_history, companion_state, config_runtime, create_app, dispatch, get_engine, health, health_v1, icon_file, lifespan, manifest, observability_health, observability_ready, pairing_info, pairing_pair, prepared_pending, root, runs, runtime_scoreboard_view, runtime_status, service_worker, service_worker_head, sovereign_dispatch, styles_file, styles_head, system_log
- Classes (3): DispatchRequest, PairRequest, SovereignDispatch
- Constants (12): BASE_DIR, DATA_DIR, OFFLINE_MODE, OPERATOR_PIN, ROOT_DIR, START_TIME, UI_DIR, VERBOSE, _ICON_SVG, _MANIFEST, _PWA_SHELL, _SW_JS
- Exports (0): -

### nexusmon_runtime.api.system
- Path: nexusmon_runtime/api/system.py
- Functions (4): get_health, get_omens, get_predictions, get_templates
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.v1_stubs
- Path: nexusmon_runtime/api/v1_stubs.py
- Functions (2): get_ai_status, get_prepared_pending
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.api.verify_routes
- Path: nexusmon_runtime/api/verify_routes.py
- Functions (8): _require_operator, patchpack_apply, patchpack_generate, patchpack_rollback, verify_kernel, verify_replay, verify_run, verify_status
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.arena
- Path: nexusmon_runtime/arena/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.arena.config
- Path: nexusmon_runtime/arena/config.py
- Functions (3): load_config, save_config, self_check
- Classes (0): -
- Constants (3): _CONFIG_PATH, _DATA_DIR, _DEFAULT_CONFIG
- Exports (0): -

### nexusmon_runtime.arena.engine
- Path: nexusmon_runtime/arena/engine.py
- Functions (1): _generate_response
- Classes (1): ArenaEngine
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.arena.schema
- Path: nexusmon_runtime/arena/schema.py
- Functions (0): -
- Classes (5): ArenaCandidate, ArenaConfig, ArenaRun, ArenaRunStatus, CandidateStatus
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.arena.scoring
- Path: nexusmon_runtime/arena/scoring.py
- Functions (4): _score_length, _score_length_quality, rank_candidates, score_candidate
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.arena.store
- Path: nexusmon_runtime/arena/store.py
- Functions (0): -
- Classes (1): ArenaStore
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.arena.ui
- Path: nexusmon_runtime/arena/ui.py
- Functions (1): arena_ui
- Classes (0): -
- Constants (1): _ARENA_HTML
- Exports (0): -

### nexusmon_runtime.avatar.avatar_omega
- Path: nexusmon_runtime/avatar/avatar_omega.py
- Functions (0): -
- Classes (3): AvatarInfinity, AvatarOmega, AvatarOmegaPlus
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.avatar.operator_link
- Path: nexusmon_runtime/avatar/operator_link.py
- Functions (0): -
- Classes (1): OperatorLink
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core
- Path: nexusmon_runtime/core/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.authority
- Path: nexusmon_runtime/core/authority.py
- Functions (7): _evaluate_attention, _evaluate_compute_cost, _evaluate_economic_value, _evaluate_maintainability, _evaluate_prediction_confidence, _evaluate_trust, validate_transaction
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.autoloop
- Path: nexusmon_runtime/core/autoloop.py
- Functions (0): -
- Classes (1): AutoLoopManager
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.brain
- Path: nexusmon_runtime/core/brain.py
- Functions (0): -
- Classes (2): BrainMapping, BrainRole
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.cadence
- Path: nexusmon_runtime/core/cadence.py
- Functions (0): -
- Classes (1): CadenceEngine
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.engine
- Path: nexusmon_runtime/core/engine.py
- Functions (0): -
- Classes (1): NexusmonEngine
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.infra_autoscale
- Path: nexusmon_runtime/core/infra_autoscale.py
- Functions (1): compute_autoscale_recommendations
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.infra_backup
- Path: nexusmon_runtime/core/infra_backup.py
- Functions (2): _extract_resources, compute_backup_plan
- Classes (0): -
- Constants (1): _RESOURCE_KEYS
- Exports (0): -

### nexusmon_runtime.core.infra_metrics
- Path: nexusmon_runtime/core/infra_metrics.py
- Functions (2): build_infra_overview, record_infra_metrics
- Classes (0): -
- Constants (1): _METRIC_FIELDS
- Exports (0): -

### nexusmon_runtime.core.infra_missions
- Path: nexusmon_runtime/core/infra_missions.py
- Functions (3): _new_mission_id, _save_mission, emit_infra_missions
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.infra_model
- Path: nexusmon_runtime/core/infra_model.py
- Functions (0): -
- Classes (18): BackupJob, BlockchainNode, CloudSubscription, ColoAllocation, ContainerInstance, CoolingZone, DRPlan, DataCenter, GPUCluster, GPUNode, MiningJob, NetworkSegment, PowerFeed, Rack, ServerNode, StorageArray, Tenant, VMInstance
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.learning
- Path: nexusmon_runtime/core/learning.py
- Functions (0): -
- Classes (1): LearningEngine
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.maintenance
- Path: nexusmon_runtime/core/maintenance.py
- Functions (0): -
- Classes (1): MaintenanceScheduler
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.mission_engine_v4
- Path: nexusmon_runtime/core/mission_engine_v4.py
- Functions (0): -
- Classes (4): DSLExecutor, DSLParser, DSLReporter, DSLValidator
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.operator_forge_v4
- Path: nexusmon_runtime/core/operator_forge_v4.py
- Functions (0): -
- Classes (2): DomainBlueprint, OperatorForgeV4
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.prediction
- Path: nexusmon_runtime/core/prediction.py
- Functions (0): -
- Classes (1): ProphetEngine
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.reality_engine_v4
- Path: nexusmon_runtime/core/reality_engine_v4.py
- Functions (0): -
- Classes (2): PhysicsLayer, RealityEngineV4
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.resonance
- Path: nexusmon_runtime/core/resonance.py
- Functions (0): -
- Classes (1): ResonanceDetector
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.scoring
- Path: nexusmon_runtime/core/scoring.py
- Functions (4): calculate_expected_value, calculate_leverage_score, rank_missions, should_execute
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.swarm_engine_v3
- Path: nexusmon_runtime/core/swarm_engine_v3.py
- Functions (0): -
- Classes (1): SwarmEngineV3
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.swarm_engine_v4
- Path: nexusmon_runtime/core/swarm_engine_v4.py
- Functions (0): -
- Classes (4): FormationExecutor, FormationMonitor, FormationRuleset, FormationSynthesizer
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.telemetry
- Path: nexusmon_runtime/core/telemetry.py
- Functions (8): _append, avg_duration, last_event, record_duration, record_event, record_failure, set_verbose, verbose_log
- Classes (0): -
- Constants (3): DATA_DIR, RUNTIME_METRICS_FILE, TELEMETRY_FILE
- Exports (0): -

### nexusmon_runtime.core.universe_mesh_v2
- Path: nexusmon_runtime/core/universe_mesh_v2.py
- Functions (0): -
- Classes (4): CosmicMap, CosmicRouter, CosmologyNode, InterCosmicLink
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.core.visibility
- Path: nexusmon_runtime/core/visibility.py
- Functions (0): -
- Classes (1): VisibilityManager
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.cosmology.cosmology_v3
- Path: nexusmon_runtime/cosmology/cosmology_v3.py
- Functions (0): -
- Classes (2): CosmologyTicker, DynamicNode
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.cosmology.energy_model
- Path: nexusmon_runtime/cosmology/energy_model.py
- Functions (0): -
- Classes (1): EnergyModel
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.cosmology.entropy_model
- Path: nexusmon_runtime/cosmology/entropy_model.py
- Functions (0): -
- Classes (1): EntropyModel
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.cosmology.kernel_types
- Path: nexusmon_runtime/cosmology/kernel_types.py
- Functions (0): -
- Classes (1): KernelTypes
- Constants (1): COSMOLOGY_STATES
- Exports (0): -

### nexusmon_runtime.factory.engine
- Path: nexusmon_runtime/factory/engine.py
- Functions (10): _append, _read_jsonl, _update_mission, execute_artifact, get_mission, intake, latest_decision, list_missions, mermaid_graph, record_decision
- Classes (0): -
- Constants (4): DATA_DIR, DECISIONS_FILE, FACTORY_FILE, GUILDS
- Exports (0): -

### nexusmon_runtime.hyper_fabric_engine_v1
- Path: nexusmon_runtime/hyper_fabric_engine_v1.py
- Functions (0): -
- Classes (1): HyperFabricEngineV1
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.integration.integration_map
- Path: nexusmon_runtime/integration/integration_map.py
- Functions (0): -
- Classes (1): IntegrationMap
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.kernel.federation
- Path: nexusmon_runtime/kernel/federation.py
- Functions (0): -
- Classes (2): FederationRouter, KernelRegistry
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.meta
- Path: nexusmon_runtime/meta/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (2): LatticeFlow, MetaSelector

### nexusmon_runtime.meta.selector
- Path: nexusmon_runtime/meta/selector.py
- Functions (2): get_engine, set_engine_provider
- Classes (8): ArchitecturalRestraint, LatticeFlow, MagicWay, MetaSelector, MythicalWay, PreEvaluated, SovereignOverride, SpaceShaping
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.meta.task_matrix
- Path: nexusmon_runtime/meta/task_matrix.py
- Functions (2): get_engine, set_engine_provider
- Classes (10): ArchitecturalRestraintLayer, HiddenWayLayer, MagicWayLayer, MythicalWayLayer, NextTaskMatrix, PreEvaluatedLayer, SovereignArbitrationLayer, SpaceShapingLayer, StabilizingLayer, UniversalGiftLayer
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.mission_engine.mission_engine
- Path: nexusmon_runtime/mission_engine/mission_engine.py
- Functions (0): -
- Classes (1): MissionEngine
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.mission_engine.mission_engine_v3
- Path: nexusmon_runtime/mission_engine/mission_engine_v3.py
- Functions (0): -
- Classes (4): GraphBuilder, GraphExecutor, GraphMonitor, GraphReporter
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.mission_engine_v1
- Path: nexusmon_runtime/mission_engine_v1.py
- Functions (0): -
- Classes (1): MissionEngineV1
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.omni_fabric_engine_v5
- Path: nexusmon_runtime/omni_fabric_engine_v5.py
- Functions (0): -
- Classes (1): OmniFabricEngineV5
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.orchestrator.orchestrator
- Path: nexusmon_runtime/orchestrator/orchestrator.py
- Functions (2): _extract_output_text, crew_from_config
- Classes (5): Agent, Crew, CrewResult, OpenAIResponsesClient, Task
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.session.operator_session
- Path: nexusmon_runtime/session/operator_session.py
- Functions (0): -
- Classes (1): OperatorSession
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.session.session_router
- Path: nexusmon_runtime/session/session_router.py
- Functions (3): end_session, get_session_state, start_session
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.session.session_store
- Path: nexusmon_runtime/session/session_store.py
- Functions (0): -
- Classes (1): SessionStore
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.shadow_ledger.shadow_ledger
- Path: nexusmon_runtime/shadow_ledger/shadow_ledger.py
- Functions (0): -
- Classes (1): ShadowLedger
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.storage
- Path: nexusmon_runtime/storage/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.storage.db
- Path: nexusmon_runtime/storage/db.py
- Functions (0): -
- Classes (1): Database
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.storage.infra_state
- Path: nexusmon_runtime/storage/infra_state.py
- Functions (5): _to_dict, append_infra_event, load_infra_events, load_infra_state, save_infra_state
- Classes (0): -
- Constants (3): DATA_DIR, INFRA_EVENTS_PATH, INFRA_STATE_PATH
- Exports (0): -

### nexusmon_runtime.storage.jsonl_utils
- Path: nexusmon_runtime/storage/jsonl_utils.py
- Functions (4): _quarantine_log, append_jsonl, read_jsonl, write_jsonl
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.storage.schema
- Path: nexusmon_runtime/storage/schema.py
- Functions (0): -
- Classes (11): AuditEntry, CrossLayerScores, MaintenanceTask, Mission, MissionCategory, MissionStatus, Omen, Prophecy, Rune, TransactionValidation, VisibilityLevel
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.supra_fabric_engine_v1
- Path: nexusmon_runtime/supra_fabric_engine_v1.py
- Functions (0): -
- Classes (1): SupraFabricEngineV1
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.swarm_engine.behaviors
- Path: nexusmon_runtime/swarm_engine/behaviors.py
- Functions (0): -
- Classes (4): Guardian, Navigator, Scout, Worker
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.swarm_engine.formations
- Path: nexusmon_runtime/swarm_engine/formations.py
- Functions (0): -
- Classes (5): ClusterFormation, Formation, GridFormation, LineFormation, ThreadFormation
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.ui.cockpit
- Path: nexusmon_runtime/ui/cockpit.py
- Functions (2): get_cockpit_layout, get_cockpit_panels
- Classes (0): -
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.universe_mesh.universe_mesh
- Path: nexusmon_runtime/universe_mesh/universe_mesh.py
- Functions (0): -
- Classes (3): MeshLink, MeshRouter, WorldNode
- Constants (0): -
- Exports (0): -

### nexusmon_runtime.verify.patchpacks
- Path: nexusmon_runtime/verify/patchpacks.py
- Functions (3): apply_patchpack, generate_patchpack, rollback_patchpack
- Classes (0): -
- Constants (1): PACK_ROOT
- Exports (0): -

### nexusmon_runtime.verify.provenance
- Path: nexusmon_runtime/verify/provenance.py
- Functions (4): _hash_entry, _last_hash, append_audit, verify_chain
- Classes (0): -
- Constants (2): AUDIT_FILE, SEAL_KEY_ENV
- Exports (0): -

### nexusmon_runtime.verify.runner
- Path: nexusmon_runtime/verify/runner.py
- Functions (6): _read_jsonl, replay_audit, run_status, run_verify, verify_invariants, verify_kernel_integrity
- Classes (0): -
- Constants (2): DATA_DIR, VERIFY_DIR
- Exports (0): -

### nexusmon_runtime.verify.scheduler
- Path: nexusmon_runtime/verify/scheduler.py
- Functions (6): _append_run, _load_state, _save_state, pause, resume, tick
- Classes (0): -
- Constants (3): DATA_DIR, RUNS_FILE, SCHED_FILE
- Exports (0): -

### nexusmon_server
- Path: nexusmon_server.py
- Functions (35): _utc_now_iso_z, admin_honeypot, admin_secret_honeypot, apple_touch_icon, auth_login, auth_me, companion_message, compute_phase, console_page, create_mission, execute_task, galileo_experiments, galileo_hypotheses, galileo_run, galileo_run_details, galileo_run_experiment, galileo_selfcheck, get_audit_log, get_lan_ip, health_check, home_page, icon_svg, json_exception_handler, list_missions, list_tasks, main, manifest, pwa_manifest, pwa_service_worker, run_mission, security_status, service_worker, system_info, traceback_last, ui_state
- Classes (4): LoginRequest, MissionCreateRequest, TaskExecuteRequest, TaskExecuteResponse
- Constants (2): LAN_IP, SERVER_PORT
- Exports (0): -

### test_arena
- Path: test_arena.py
- Functions (1): test_arena
- Classes (6): TestArenaAPI, TestArenaConfig, TestArenaEngine, TestArenaSchema, TestArenaScoring, TestArenaStore
- Constants (0): -
- Exports (0): -

### test_companion
- Path: test_companion.py
- Functions (1): run_companion_tests
- Classes (10): TestCommitEngine, TestCompanionMode, TestEvolutionMechanism, TestIntelligenceLayer, TestModeManager, TestOperatorMode, TestNexusmonCompanion, TestSystemModes, TestTaskContext, TestWorkerSwarm
- Constants (0): -
- Exports (0): -

### test_console_endpoints
- Path: test_console_endpoints.py
- Functions (1): test_console_endpoints
- Classes (0): -
- Constants (0): -
- Exports (0): -

### test_ecosystem
- Path: test_ecosystem.py
- Functions (2): run_tests, test_ecosystem
- Classes (2): TestAutoLoopManager, TestEcosystemEndpoints
- Constants (0): -
- Exports (0): -

### test_galileo
- Path: test_galileo.py
- Functions (2): test_galileo, test_galileo_endpoints
- Classes (0): -
- Constants (1): BASE_URL
- Exports (0): -

### test_integration
- Path: test_integration.py
- Functions (1): test_integration
- Classes (1): TestCompanionCoreIntegration
- Constants (0): -
- Exports (0): -

### test_kernel_ignition
- Path: test_kernel_ignition.py
- Functions (1): test_kernel_ignition
- Classes (0): -
- Constants (0): -
- Exports (0): -

### test_mission_jsonl_robust
- Path: test_mission_jsonl_robust.py
- Functions (1): _smoke_test
- Classes (5): TestAppendJsonl, TestDatabaseRobustJsonl, TestMissionCreate, TestReadJsonl, TestWriteJsonl
- Constants (1): _DIR
- Exports (0): -

### test_runtime_infra
- Path: test_runtime_infra.py
- Functions (1): test_runtime_infra
- Classes (1): TestRuntimeInfraAPI
- Constants (0): -
- Exports (0): -

### test_nexusmon
- Path: test_nexusmon.py
- Functions (1): run_tests
- Classes (5): TestBrainMapping, TestOperatorSovereignty, TestPlugins, TestNexusmonCore, TestTaskExecutor
- Constants (0): -
- Exports (0): -

### test_nexusmon_server
- Path: test_nexusmon_server.py
- Functions (2): main, test_nexusmon_server
- Classes (1): TestWebServer
- Constants (0): -
- Exports (0): -

### test_ui
- Path: test_ui.py
- Functions (1): test_ui
- Classes (5): TestUIApiAudit, TestUIApiCapabilities, TestUIApiExecute, TestUIApiInfo, TestUIPage
- Constants (0): -
- Exports (0): -

### test_verification_runner
- Path: test_verification_runner.py
- Functions (4): _make_action, _put_state, components, tmp_data
- Classes (5): TestDeltaEvaluator, TestHelpers, TestInMemoryJobStore, TestVerificationRunnerInProcess, TestVerificationStoreQueries
- Constants (1): _DIR
- Exports (0): -

### tests.conftest
- Path: tests/conftest.py
- Functions (1): client
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_activity_stream
- Path: tests/test_activity_stream.py
- Functions (1): test_initialize_activity_stream
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_ai_audit
- Path: tests/test_ai_audit.py
- Functions (3): test_log_decision, test_log_model_call, test_sequence_numbers_increment
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_companion_master
- Path: tests/test_companion_master.py
- Functions (5): test_ensure_master, test_get_composite_context, test_record_insight, test_record_mission_observed, test_self_assessment
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_config_loader
- Path: tests/test_config_loader.py
- Functions (6): test_companion_section, test_env_override_offline, test_get_shorthand, test_is_offline_default, test_load_returns_dict, test_models_section
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_context_pack
- Path: tests/test_context_pack.py
- Functions (6): test_after_mission, test_before_mission, test_companion_selftest, test_daily_tick, test_get_scoreboard, test_load_engines
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_core_safety
- Path: tests/test_core_safety.py
- Functions (10): test_atomic_append_jsonl, test_atomic_write_json, test_cold_start_idempotent, test_schema_guard_missing_field, test_schema_guard_optional, test_schema_guard_valid, test_schema_guard_wrong_type, test_time_source_mission_timestamp, test_time_source_now, test_time_source_today
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_e2e
- Path: tests/test_e2e.py
- Functions (35): _get_test_client, test_addons_import, test_api_audit_tail, test_api_companion_state, test_api_dispatch_requires_key, test_api_dispatch_with_key, test_api_health, test_api_pairing_flow, test_api_pairing_info, test_api_runs_list, test_api_runtime_config, test_api_runtime_scoreboard, test_api_runtime_status, test_api_sovereign_dispatch, test_api_system_log, test_api_v1_health, test_commit_engine_evaluate, test_companion_conversation_mode, test_companion_import, test_core_engine_import, test_core_orchestrator_import, test_core_nexusmon_import, test_crew_from_config, test_crew_kickoff_simulation, test_dispatch_roundtrip, test_engine_instantiation, test_engine_subsystems_present, test_master_ai_simulation, test_operator_sovereignty, test_plugins_import, test_nexusmon_core_capabilities, test_task_executor, test_ui_config_runtime, test_ui_root, test_worker_swarm_workflow
- Classes (0): -
- Constants (1): ROOT
- Exports (0): -

### tests.test_engines
- Path: tests/test_engines.py
- Functions (10): test_counterfactual_engine, test_divergence_engine, test_entropy_monitor, test_evolution_memory, test_operator_anchor, test_perf_ledger, test_phase_engine, test_relevance_engine, test_trajectory_engine, test_world_model
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_hologram
- Path: tests/test_hologram.py
- Functions (3): _make_trial, _make_trials, _now_iso
- Classes (12): TestBurstMode, TestCurrencies, TestDeltaGraph, TestDrift, TestEffects, TestLevel, TestLevelsInfo, TestPowers, TestSuggestions, TestVerdict, TestWhyFailed, TestXP
- Constants (0): -
- Exports (0): -

### tests.test_ignition
- Path: tests/test_ignition.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_jsonl_utils
- Path: tests/test_jsonl_utils.py
- Functions (3): test_read_jsonl_returns_tuple_empty_file, test_read_jsonl_returns_tuple_missing_file, test_read_jsonl_returns_tuple_normal_file
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_master_ai
- Path: tests/test_master_ai.py
- Functions (0): -
- Classes (1): TestMasterAI
- Constants (0): -
- Exports (0): -

### tests.test_observability
- Path: tests/test_observability.py
- Functions (11): test__dump_routes, test_ai_status_includes_phase, test_companion_history, test_companion_state, test_debug_routes, test_health, test_observability_health, test_observability_ready, test_prepared_pending, test_prepared_pending_filtered, test_runtime_scoreboard
- Classes (1): TestObservabilityEndpoints
- Constants (0): -
- Exports (0): -

### tests.test_orchestrator
- Path: tests/test_orchestrator.py
- Functions (0): -
- Classes (1): TestNexusmonOrchestrator
- Constants (0): -
- Exports (0): -

### tests.test_promotion_path
- Path: tests/test_promotion_path.py
- Functions (0): -
- Classes (1): TestPromotionPath
- Constants (0): -
- Exports (0): -

### tests.test_runtime_ignition
- Path: tests/test_runtime_ignition.py
- Functions (0): -
- Classes (1): TestRuntimeIgnition
- Constants (0): -
- Exports (0): -

### tests.test_safe_execution
- Path: tests/test_safe_execution.py
- Functions (7): test_count_pending, test_list_pending, test_mark_executed, test_prepare_action_creates_files, test_tool_gate, test_tool_gate_message, test_tool_gate_purchase
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_storage_resilience_legacy
- Path: tests/test_storage_resilience_legacy.py
- Functions (2): _seed_corrupt_missions, test_storage_resilience_legacy
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tests.test_trials
- Path: tests/test_trials.py
- Functions (42): _backup, _clear, _restore, setup_module, teardown_module, test_add_note, test_append_only_no_rewrite, test_audit_only_grows, test_audit_trail_written, test_auto_baseline_locked_at_lv0, test_auto_baseline_unlocked_at_lv1, test_auto_check_scheduler_requires_lv2, test_auto_check_scheduler_runs_at_lv2, test_compute_survival_scores, test_create_followup, test_get_audit_trail, test_get_audit_trail_by_trial_id, test_get_survival_leaderboard, test_get_trial_by_id, test_get_trial_missing, test_inbox_completed_empty_initially, test_inbox_counts, test_inbox_needs_review_empty_initially, test_inbox_pending, test_list_available_metrics, test_load_all_trials, test_new_trial_creates_valid_record, test_rank_suggestions, test_register_custom_metric, test_require_trial_creates, test_require_trial_exemption_admin, test_require_trial_exemption_non_admin_raises, test_resolve_metric_builtin, test_resolve_metric_unknown, test_revert_nonexistent, test_revert_trial, test_survival_scores_persisted, test_trial_persisted_to_file, test_update_trial_appends, test_worker_evaluate_trial, test_worker_start_stop, test_worker_status
- Classes (0): -
- Constants (5): AUDIT_FILE, BACKUP_DIR, SCORES_FILE, TRIALS_DATA_DIR, TRIALS_FILE
- Exports (0): -

### theorem_kb
- Path: theorem_kb/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools
- Path: tools/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.build_bypass_map
- Path: tools/build_bypass_map.py
- Functions (1): main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.build_macro
- Path: tools/build_macro.py
- Functions (1): main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.daily_cycle
- Path: tools/daily_cycle.py
- Functions (2): main, run
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.doctor
- Path: tools/doctor.py
- Functions (5): _section, get_runtime_status, main, run_cmd, tail_file
- Classes (0): -
- Constants (8): AUDIT_PATH, DATA_DIR, ENABLE_PROFILING, PROFILE_PATH, ROOT, RUNTIME_CHECK, RUN_NEXUSMON, STATUS_URL
- Exports (0): -

### tools.doctor.doctor
- Path: tools/doctor/doctor.py
- Functions (7): check_port, find_errors_in_log, get_lan_ip, load_config, main, section, tail_file
- Classes (0): -
- Constants (4): CONFIG_PATH, DATA_DIR, LOG_FILES, ROOT
- Exports (0): -

### tools.find_import_cycles
- Path: tools/find_import_cycles.py
- Functions (9): build_graph, collect_imports, find_cycles, iter_py_files, main, module_name_for_file, resolve_from_import, tarjans_scc, write_dot
- Classes (0): -
- Constants (1): EXCLUDE_DIRS
- Exports (0): -

### tools.generate_python_symbol_index
- Path: tools/generate_python_symbol_index.py
- Functions (3): is_excluded, module_name_from_path, parse_file
- Classes (0): -
- Constants (4): EXCLUDED_DIRS, OUT_JSON, OUT_MD, ROOT
- Exports (0): -

### tools.generate_replay
- Path: tools/generate_replay.py
- Functions (1): generate_replay
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.install_service
- Path: tools/install_service.py
- Functions (4): install_linux_service, install_macos_service, install_service, install_windows_service
- Classes (0): -
- Constants (1): LOG_PATH
- Exports (0): -

### tools.make_evidence_pack
- Path: tools/make_evidence_pack.py
- Functions (1): generate_evidence_pack
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.make_icons
- Path: tools/make_icons.py
- Functions (2): main, write_png
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.mine_sequences
- Path: tools/mine_sequences.py
- Functions (1): main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.normalize_events
- Path: tools/normalize_events.py
- Functions (1): normalize_events
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.prune_logs
- Path: tools/prune_logs.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.pwa_self_check
- Path: tools/pwa_self_check.py
- Functions (2): fetch, main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.rotate_logs
- Path: tools/rotate_logs.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.runtime_check
- Path: tools/runtime_check.py
- Functions (6): build_status, detect_busy_loops, main, print_human_output, read_last_line, run_short_mission
- Classes (0): -
- Constants (2): DEFAULT_DATA_DIR, ROOT
- Exports (0): -

### tools.scan_anomalies
- Path: tools/scan_anomalies.py
- Functions (1): main
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.self_check
- Path: tools/self_check.py
- Functions (11): check_bom_in_json, check_cwd, check_expected_files, check_nested_package_json, check_port_conflicts, check_scripts_and_deps, err, find_package_json, info, main, warn
- Classes (0): -
- Constants (4): DEFAULT_PORTS, EXPECTED_FILES, IGNORE_DIRS, ROOT
- Exports (0): -

### tools.self_test_new_layers
- Path: tools/self_test_new_layers.py
- Functions (1): test_activity_stream
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.self_test_parallel_route
- Path: tools/self_test_parallel_route.py
- Functions (6): generate_synthetic_events, main, run_tool, verify_anomalies, verify_bypass_map, verify_sequences
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.show_mobile_qr
- Path: tools/show_mobile_qr.py
- Functions (2): generate_qr_code, get_local_ip
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.smoke.run_smoke
- Path: tools/smoke/run_smoke.py
- Functions (4): get, load_cfg, main, post_json
- Classes (1): SmokeRunner
- Constants (2): CONFIG, ROOT
- Exports (0): -

### tools.nexusmon_doctor
- Path: tools/nexusmon_doctor.py
- Functions (14): _load_runtime_config, _ports_in_use, _print_header, check_bom, check_env_and_config, check_health, check_ports, check_scripts, check_shadow_dirs, check_workdir, check_writable_dirs, main, print_result, run_self_check
- Classes (1): CheckResult
- Constants (5): CONFIG_DIR, DATA_DIR, DEFAULT_PORTS, ROOT, RUNTIME_CONFIG
- Exports (0): -

### tools.nexusmon_onboard
- Path: tools/nexusmon_onboard.py
- Functions (10): _lan_ip, ensure_anchor, main, prompt_bind, prompt_offline, prompt_port, run_doctor, start_server_once, wait_for_health, write_runtime_config
- Classes (0): -
- Constants (3): CONFIG_PATH, DATA_DIR, ROOT
- Exports (0): -

### tools.sync_logs
- Path: tools/sync_logs.py
- Functions (1): sync_logs
- Classes (0): -
- Constants (1): SYNC_FOLDERS
- Exports (0): -

### tools.test_doctor_smoke
- Path: tools/test_doctor_smoke.py
- Functions (1): main
- Classes (0): -
- Constants (2): DOCTOR, ROOT
- Exports (0): -

### tools.test_zapier_bridge
- Path: tools/test_zapier_bridge.py
- Functions (3): load_config, main, post_json
- Classes (0): -
- Constants (2): CONFIG, ROOT
- Exports (0): -

### tools.validate_events
- Path: tools/validate_events.py
- Functions (1): validate_events
- Classes (0): -
- Constants (0): -
- Exports (0): -

### tools.verify_activity_stream
- Path: tools/verify_activity_stream.py
- Functions (1): verify_activity_stream
- Classes (0): -
- Constants (1): EVENTS_FILE
- Exports (0): -

### tools.vscode-scaffold-bot.templates.module_fastapi_router.files
- Path: tools/vscode-scaffold-bot/templates/module_fastapi_router/files/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -

### ui
- Path: ui/__init__.py
- Functions (0): -
- Classes (0): -
- Constants (0): -
- Exports (0): -


