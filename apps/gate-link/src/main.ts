async function boot(): Promise<void> {
  const [{ default: Phaser }, { GameScene }] = await Promise.all([
    import("phaser"),
    import("./scenes/GameScene"),
  ]);

  new Phaser.Game({
    type: Phaser.AUTO,
    parent: "app",
    width: 900,
    height: 520,
    backgroundColor: "#050814",
    scene: [GameScene],
  });
}

void boot();
