export type HookName =
  | "on_invoke"
  | "on_consult"
  | "on_symbolic_interpretation"
  | "on_generate_geometry"
  | "on_trigger_anomaly"
  | "on_resolve_correspondence"
  | "on_render_altar_mode"
  | "on_simulate_branch";

export type CockpitModeRoute = {
  buttonId: string;
  modeId: string;
  hook: HookName;
  endpoint: string;
  systemId: string;
};

export const MODE_ROUTES: CockpitModeRoute[] = [
  {
    buttonId: "activate-pantheon",
    modeId: "pantheon_browser",
    hook: "on_invoke",
    endpoint: "/v1/nexusmon/symbolic/activate/{id}",
    systemId: "pantheon.norse.odin",
  },
  {
    buttonId: "consult-grimoire",
    modeId: "grimoire_viewer",
    hook: "on_consult",
    endpoint: "/v1/nexusmon/symbolic/consult",
    systemId: "grimoire.ars_notoria",
  },
  {
    buttonId: "render-sigil",
    modeId: "sigil_renderer",
    hook: "on_generate_geometry",
    endpoint: "/v1/nexusmon/symbolic/geometry",
    systemId: "sigil.triadic_seed",
  },
  {
    buttonId: "invoke-relic",
    modeId: "relic_inventory",
    hook: "on_invoke",
    endpoint: "/v1/nexusmon/symbolic/invoke",
    systemId: "relic.operator_compass",
  },
  {
    buttonId: "consult-cosmic",
    modeId: "cosmic_hud",
    hook: "on_consult",
    endpoint: "/v1/nexusmon/symbolic/consult",
    systemId: "archive.cosmic_mind.model_01",
  },
  {
    buttonId: "simulate-branch",
    modeId: "multiverse_viewer",
    hook: "on_simulate_branch",
    endpoint: "/v1/nexusmon/symbolic/branch",
    systemId: "multiverse.fork_alpha",
  },
  {
    buttonId: "trigger-synchronicity",
    modeId: "synchronicity_web",
    hook: "on_trigger_anomaly",
    endpoint: "/v1/nexusmon/symbolic/anomaly",
    systemId: "synchronicity.core",
  },
  {
    buttonId: "refresh-lineage",
    modeId: "lineage_tree",
    hook: "on_consult",
    endpoint: "/v1/nexusmon/symbolic/lineage",
    systemId: "lineage.ancestral_shards",
  },
  {
    buttonId: "render-altar-mode",
    modeId: "altar_modes",
    hook: "on_render_altar_mode",
    endpoint: "/v1/nexusmon/symbolic/altar",
    systemId: "altar.neon_observatory",
  },
  {
    buttonId: "mirror-reflect",
    modeId: "sovereign_mirror_panel",
    hook: "on_consult",
    endpoint: "/v1/nexusmon/life/sovereign_mirror/reflect",
    systemId: "life.sovereign_mirror",
  },
  {
    buttonId: "build-memory-room",
    modeId: "memory_palace_explorer",
    hook: "on_symbolic_interpretation",
    endpoint: "/v1/nexusmon/life/memory_palace/build",
    systemId: "life.memory_palace",
  },
];
