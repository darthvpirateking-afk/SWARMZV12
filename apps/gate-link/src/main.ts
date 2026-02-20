import Phaser from "phaser";
import { GameScene } from "./scenes/GameScene";

const game = new Phaser.Game({
  type: Phaser.AUTO,
  parent: "app",
  width: 900,
  height: 520,
  backgroundColor: "#050814",
  scene: [GameScene],
});

export default game;
