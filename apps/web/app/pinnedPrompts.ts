export type PinnedDemo = {
  id: string;
  label: string;
  prompt: string;
  expect: { cards: Array<"howto"|"concept"|"plan"|"reference">; tools: string[] };
};

export const PINNED_DEMOS: PinnedDemo[] = [
  { id: "uni-knot", label: "Uni Knot", prompt: "Teach me to tie a Uni Knot for 20 lb mono, step by step.", expect: { cards: ["howto","reference"], tools: ["images"] } },
  { id: "surf-rig", label: "Surf Rig (Whiting)", prompt: "Set up a beginner surf fishing rig for whiting on light gear.", expect: { cards: ["howto","reference"], tools: ["images"] } },
  { id: "clarence-plan", label: "Clarence — 2-Day Plan", prompt: "Plan a 2-day fishing trip on the Clarence River (shore + small tinny).", expect: { cards: ["plan","reference"], tools: ["weather","marine","images","search"] } },
  { id: "estuary-conditions", label: "Estuary Conditions", prompt: "Assess wind/swell for a safe estuary mouth session at Yamba on Saturday morning.", expect: { cards: ["plan","reference"], tools: ["weather","marine"] } },
  { id: "lachlan-orogen", label: "Lachlan Orogen", prompt: "Explain the Lachlan Orogen in simple terms with key events.", expect: { cards: ["concept"], tools: ["images","search"] } },
  { id: "rock-id", label: "Rock ID Checklist", prompt: "Create a field checklist for basic rock identification (hand lens only).", expect: { cards: ["reference","howto"], tools: ["images"] } },
  { id: "knife-sharpen", label: "Sharpen Knife", prompt: "Sharpen a chef's knife safely with a whetstone (grits 1000/3000).", expect: { cards: ["howto","reference"], tools: ["images"] } },
  { id: "kayak-safety", label: "Kayak Safety", prompt: "Kayak pre-launch safety checklist for tidal rivers.", expect: { cards: ["reference"], tools: ["images"] } },
  { id: "py-list-dict", label: "Python Lists vs Dicts", prompt: "Python: lists vs dicts — when to use which, with tiny examples.", expect: { cards: ["reference"], tools: [] } },
  { id: "git-pr", label: "Git PR Flow", prompt: "Step-by-step: create a feature branch, commit, and open a PR.", expect: { cards: ["howto"], tools: [] } },
  { id: "spanish-past", label: "Spanish Past Tenses", prompt: "Spanish preterite vs imperfect — quick cheat sheet with 3 examples.", expect: { cards: ["reference"], tools: [] } },
  { id: "10k-taper", label: "10k Taper Plan", prompt: "Plan a 7-day taper for a 10 km trail race (beginner).", expect: { cards: ["plan","reference"], tools: [] } },
  { id: "native-bed", label: "Native Bed (Sydney)", prompt: "Design a 2×4 m native-plant bed for Sydney: layout, soil prep, watering.", expect: { cards: ["plan","reference"], tools: ["images","search"] } },
  { id: "drone-au", label: "Drone Rules (AU)", prompt: "Recreational drone rules in Australia — quick reference with safe checklist.", expect: { cards: ["reference","howto"], tools: ["search","images"] } }
];

