import Phaser from "phaser";
import {
  applyGateRewards,
  loadProgress,
  resetProgress,
  type PlayerProgress,
} from "../state/progression";
import {
  createMission,
  resolveMissionReward,
  type GateMission,
} from "../systems/mission";

const GRID_SIZE = 5;
const CELL = 64;
const GRID_X = 48;
const GRID_Y = 96;

type GridPos = { x: number; y: number };

type Chip = {
  name: string;
  effect: "damage" | "heal" | "buff" | "summon";
  value: number;
};

export class GameScene extends Phaser.Scene {
  private progress!: PlayerProgress;
  private mission!: GateMission;
  private missionTimer = 0;

  private partnerPos: GridPos = { x: 2, y: 2 };
  private enemyPos: GridPos = { x: 2, y: 2 };
  private shadowPos: GridPos = { x: 1, y: 2 };

  private partnerHp = 120;
  private enemyHp = 180;
  private shadowHp = 80;

  private chips: Chip[] = [];
  private messageText!: Phaser.GameObjects.Text;
  private hudText!: Phaser.GameObjects.Text;
  private timerText!: Phaser.GameObjects.Text;
  private partnerSprite!: Phaser.GameObjects.Rectangle;
  private enemySprite!: Phaser.GameObjects.Rectangle;
  private shadowSprite!: Phaser.GameObjects.Rectangle;
  private missionResolved = false;

  constructor() {
    super("GameScene");
  }

  create(): void {
    this.cameras.main.setBackgroundColor("#050814");

    this.progress = loadProgress();
    this.mission = createMission(this.progress.gateTier);
    this.missionTimer = this.mission.durationSeconds;

    this.drawGrid(GRID_X, GRID_Y, 0x1fd3ff);
    this.drawGrid(GRID_X + GRID_SIZE * CELL + 96, GRID_Y, 0xff5b7f);

    this.messageText = this.add.text(48, 24, "JACK-IN: Gate mission active", {
      color: "#7df9ff",
      fontSize: "18px",
    });
    this.hudText = this.add.text(48, 432, "", {
      color: "#f2f5ff",
      fontSize: "16px",
    });
    this.timerText = this.add.text(48, 460, "", {
      color: "#f8d66d",
      fontSize: "16px",
    });

    this.partnerSprite = this.add
      .rectangle(0, 0, CELL - 20, CELL - 20, 0x7df9ff)
      .setStrokeStyle(2, 0xffffff);
    this.shadowSprite = this.add
      .rectangle(0, 0, CELL - 24, CELL - 24, 0xb794f4)
      .setStrokeStyle(2, 0xffffff);
    this.enemySprite = this.add
      .rectangle(0, 0, CELL - 20, CELL - 20, 0xff5b7f)
      .setStrokeStyle(2, 0xffffff);

    this.spawnChipHand();
    this.bindInput();
    this.refreshHud();

    this.time.addEvent({
      delay: 1000,
      loop: true,
      callback: () => {
        if (this.missionResolved) return;
        this.missionTimer = Math.max(0, this.missionTimer - 1);
        this.enemyAct();
        this.shadowAct();
        this.refreshHud();
        if (this.missionTimer === 0) {
          this.endMission(this.enemyHp <= 0);
        }
      },
    });

    this.input.keyboard?.on("keydown-SPACE", () => {
      if (this.missionResolved) {
        this.scene.restart();
      }
    });

    this.input.keyboard?.on("keydown-R", () => {
      resetProgress();
      this.setMessage("Progress reset. Rebooting profile...");
      this.time.delayedCall(400, () => this.scene.restart());
    });
  }

  private drawGrid(x: number, y: number, color: number): void {
    const g = this.add.graphics();
    g.lineStyle(2, color, 0.8);
    g.fillStyle(0x0a1022, 0.7);

    for (let row = 0; row < GRID_SIZE; row += 1) {
      for (let col = 0; col < GRID_SIZE; col += 1) {
        g.fillRect(x + col * CELL, y + row * CELL, CELL - 2, CELL - 2);
        g.strokeRect(x + col * CELL, y + row * CELL, CELL, CELL);
      }
    }
  }

  private bindInput(): void {
    this.input.keyboard?.on("keydown", (ev: KeyboardEvent) => {
      if (ev.key === "ArrowUp") this.movePartner(0, -1);
      if (ev.key === "ArrowDown") this.movePartner(0, 1);
      if (ev.key === "ArrowLeft") this.movePartner(-1, 0);
      if (ev.key === "ArrowRight") this.movePartner(1, 0);
      if (ev.key === "1") this.useChip(0);
      if (ev.key === "2") this.useChip(1);
      if (ev.key === "3") this.useChip(2);
      if (ev.key.toLowerCase() === "q") this.castAbility1();
      if (ev.key.toLowerCase() === "w") this.castAbility2();
      if (ev.key.toLowerCase() === "e") this.castUltimate();
    });
  }

  private movePartner(dx: number, dy: number): void {
    this.partnerPos.x = Phaser.Math.Clamp(
      this.partnerPos.x + dx,
      0,
      GRID_SIZE - 1,
    );
    this.partnerPos.y = Phaser.Math.Clamp(
      this.partnerPos.y + dy,
      0,
      GRID_SIZE - 1,
    );
    this.setMessage(
      `Partner moved to ${this.partnerPos.x},${this.partnerPos.y}`,
    );
    this.refreshHud();
  }

  private castAbility1(): void {
    const dmg = 18 + this.progress.partnerLevel;
    this.enemyHp = Math.max(0, this.enemyHp - dmg);
    this.setMessage(`Ability 1 hit for ${dmg}`);
    this.refreshHud();
    this.checkWin();
  }

  private castAbility2(): void {
    const heal = 14 + Math.floor(this.progress.partnerLevel / 2);
    this.partnerHp = Math.min(140, this.partnerHp + heal);
    this.setMessage(`Ability 2 healed ${heal}`);
    this.refreshHud();
  }

  private castUltimate(): void {
    const dmg = 36 + this.progress.partnerLevel * 2;
    this.enemyHp = Math.max(0, this.enemyHp - dmg);
    this.setMessage(`Ultimate strike for ${dmg}`);
    this.refreshHud();
    this.checkWin();
  }

  private spawnChipHand(): void {
    const pool: Chip[] = [
      { name: "Burst", effect: "damage", value: 25 },
      { name: "Patch", effect: "heal", value: 20 },
      { name: "Overclock", effect: "buff", value: 8 },
      { name: "Echo Summon", effect: "summon", value: 15 },
    ];
    this.chips = Phaser.Utils.Array.Shuffle([...pool]).slice(0, 3);
  }

  private useChip(index: number): void {
    const chip = this.chips[index];
    if (!chip) return;

    if (chip.effect === "damage")
      this.enemyHp = Math.max(0, this.enemyHp - chip.value);
    if (chip.effect === "heal")
      this.partnerHp = Math.min(140, this.partnerHp + chip.value);
    if (chip.effect === "buff")
      this.partnerHp = Math.min(150, this.partnerHp + chip.value);
    if (chip.effect === "summon")
      this.enemyHp = Math.max(0, this.enemyHp - chip.value);

    this.setMessage(`Chip used: ${chip.name}`);
    this.chips.splice(index, 1);
    while (this.chips.length < 3) {
      const refill = Phaser.Utils.Array.Shuffle([
        { name: "Burst", effect: "damage", value: 25 },
        { name: "Patch", effect: "heal", value: 20 },
        { name: "Overclock", effect: "buff", value: 8 },
        { name: "Echo Summon", effect: "summon", value: 15 },
      ] as Chip[])[0];
      this.chips.push(refill);
    }
    this.refreshHud();
    this.checkWin();
  }

  private enemyAct(): void {
    if (this.enemyHp <= 0) return;

    const telegraph = Phaser.Math.Between(0, 100) > 65;
    if (telegraph) {
      this.setMessage("Enemy telegraph detected! Dodge now.");
      return;
    }

    const dmgToPartner = Phaser.Math.Between(8, 14);
    this.partnerHp = Math.max(0, this.partnerHp - dmgToPartner);

    if (this.shadowHp > 0 && Phaser.Math.Between(0, 100) > 60) {
      const dmgToShadow = Phaser.Math.Between(6, 10);
      this.shadowHp = Math.max(0, this.shadowHp - dmgToShadow);
    }

    if (this.partnerHp <= 0) {
      this.endMission(false);
    }
  }

  private shadowAct(): void {
    if (this.shadowHp <= 0 || this.enemyHp <= 0) return;
    const dmg =
      Phaser.Math.Between(6, 11) + Math.floor(this.progress.partnerLevel / 2);
    this.enemyHp = Math.max(0, this.enemyHp - dmg);
    this.checkWin();
  }

  private checkWin(): void {
    if (this.enemyHp <= 0) {
      this.endMission(true);
    }
  }

  private endMission(victory: boolean): void {
    if (!this.scene.isActive() || this.missionResolved) return;
    this.missionResolved = true;

    if (victory) {
      const rewards = resolveMissionReward(this.mission);
      this.progress = applyGateRewards(this.progress, rewards);
      this.setMessage(
        `Gate cleared! +${rewards.xp} XP, +${rewards.shards} Data Shards`,
      );
    } else {
      this.setMessage("Gate failed. Retreat and rebuild.");
    }

    this.time.delayedCall(1600, () => {
      this.setMessage("Mission complete. Press SPACE to redeploy.");
      this.refreshHud();
    });
  }

  private refreshHud(): void {
    this.partnerSprite.setPosition(
      this.toBoardX(this.partnerPos.x, GRID_X),
      this.toBoardY(this.partnerPos.y),
    );
    this.shadowSprite.setPosition(
      this.toBoardX(this.shadowPos.x, GRID_X),
      this.toBoardY(this.shadowPos.y),
    );
    this.enemySprite.setPosition(
      this.toBoardX(this.enemyPos.x, GRID_X + GRID_SIZE * CELL + 96),
      this.toBoardY(this.enemyPos.y),
    );

    this.partnerSprite.setVisible(this.partnerHp > 0);
    this.shadowSprite.setVisible(this.shadowHp > 0);
    this.enemySprite.setVisible(this.enemyHp > 0);

    const chipNames = this.chips
      .map((chip, i) => `[${i + 1}] ${chip.name}`)
      .join("  ");
    this.hudText.setText([
      `Partner HP: ${this.partnerHp}   Enemy HP: ${this.enemyHp}   Shadow HP: ${this.shadowHp}`,
      `Partner Form: ${this.progress.partnerForm}  Lv ${this.progress.partnerLevel}  XP ${this.progress.partnerXp}/${this.progress.partnerLevel * 100}  Data Shards: ${this.progress.dataShards}`,
      `Controls: Arrows move | Q/W/E abilities | 1/2/3 chips (${chipNames}) | SPACE redeploy | R reset save`,
    ]);
    this.timerText.setText(
      `Gate: ${this.mission.gateType} | Tier ${this.mission.tier} | Time Left: ${this.missionTimer}s`,
    );
  }

  private setMessage(message: string): void {
    this.messageText.setText(`JACK-IN: ${message}`);
  }

  private toBoardX(gridX: number, boardX: number): number {
    return boardX + gridX * CELL + CELL / 2;
  }

  private toBoardY(gridY: number): number {
    return GRID_Y + gridY * CELL + CELL / 2;
  }
}
