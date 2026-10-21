// pipeline/make-short.mjs - End-to-End YouTube Shorts Pipeline CLI
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { ROOT_DIR } from "./config.mjs";
import { generateAudio } from "./audio-generator.mjs";
import { generateComposition } from "./composition-generator.mjs";
import { renderAndMux } from "./render-and-mux.mjs";

/**
 * Generate a high-retention 4-part script structure from a raw topic/prompt.
 */
function buildScriptFromTopic(topic) {
  const cleanId = topic.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 28).replace(/^-|-$/g, "");
  const projectId = `short-${Date.now().toString().slice(-4)}-${cleanId}`;

  return {
    id: projectId,
    title: topic,
    youtubeTitle: `Stop Doing This With ${topic.slice(0, 30)}! 🤯 #Shorts`,
    youtubeDescription: `Here is the fastest zero-cost way to master ${topic} without wasting hours.`,
    voice: "en-US-ChristopherNeural",
    rate: "+4%",
    fps: 30,
    scenes: [
      {
        id: "hook",
        badge: "CRITICAL WORKFLOW",
        cardType: "hook",
        tag: "ATTENTION",
        visualTitle: `The Secret to <span style="background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${topic}</span>`,
        visualBody: "Most creators and developers waste 80% of their time on this.",
        stat: "10x",
        statLabel: "Faster Execution",
        voiceText: `If you are trying to master ${topic}, stop doing it the traditional way.`,
        sfx: "hook-impact",
      },
      {
        id: "problem",
        badge: "THE BOTTLENECK",
        cardType: "comparison",
        visualTitle: "The Common Mistake",
        oldWay: "Hours of manual configuration and paid subscriptions.",
        newWay: "Automated, zero-cost code-driven generation.",
        voiceText: "Most people get stuck paying monthly subscriptions and wrestling with slow tools.",
        sfx: "zoom-swish",
      },
      {
        id: "solution",
        badge: "THE MODERN STACK",
        cardType: "code",
        visualTitle: "The Code-Driven Solution",
        terminalTitle: "workflow.config.ts",
        codeSnippet: `const pipeline = new Studio();\nawait pipeline.execute({\n  model: "HyperFrames",\n  cost: 0,\n  speed: "Instant"\n});`,
        voiceText: "Instead, combine lightweight headless engines with zero-cost neural audio for instant results.",
        sfx: "ui-pop",
      },
      {
        id: "loop",
        badge: "VERIFIED RESULT",
        cardType: "feature",
        tag: "PAYOFF",
        visualTitle: "Ready in Seconds",
        visualBody: "Full HD 1080p, mastered at -14 LUFS, and 100% policy-compliant.",
        stat: "100%",
        statLabel: "Free & Local",
        voiceText: "And that's why you should start streamlining your entire creation loop today.",
        sfx: "clean-ding",
      },
    ],
  };
}

async function main() {
  const args = process.argv.slice(2);
  let scriptData = null;
  let customScriptPath = null;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--script" && args[i + 1]) {
      customScriptPath = path.resolve(args[i + 1]);
    } else if ((args[i] === "--prompt" || args[i] === "--topic") && args[i + 1]) {
      scriptData = buildScriptFromTopic(args[i + 1]);
    }
  }

  if (customScriptPath) {
    const raw = await fs.readFile(customScriptPath, "utf8");
    scriptData = JSON.parse(raw);
  }

  if (!scriptData) {
    // Default demo prompt if none provided
    scriptData = buildScriptFromTopic("AI Video Pipelines");
  }

  console.log(`\n==================================================`);
  console.log(`🎬 AI Simplified Lab — YouTube Shorts Generator`);
  console.log(`   Project ID: ${scriptData.id}`);
  console.log(`   Title:      ${scriptData.title}`);
  console.log(`==================================================\n`);

  const projectDir = path.join(ROOT_DIR, "projects", scriptData.id);
  const compDir = path.join(projectDir, "composition");
  await fs.mkdir(compDir, { recursive: true });

  // Save project script
  await fs.writeFile(path.join(projectDir, "script.json"), JSON.stringify(scriptData, null, 2));

  // Step 1: Generate Voiceover & Aligned SFX
  console.log(`[Step 1/3] Generating Speech and Audio Mix...`);
  const audioResult = await generateAudio(projectDir, scriptData);
  console.log(`✓ Audio complete: ${audioResult.totalDuration}s (${audioResult.totalFrames} frames @ ${audioResult.fps} fps)\n`);

  // Step 2: Build HTML & GSAP Composition
  console.log(`[Step 2/3] Synthesizing HyperFrames Composition...`);
  const compositionData = {
    ...scriptData,
    totalDuration: audioResult.totalDuration,
    totalFrames: audioResult.totalFrames,
    fps: audioResult.fps,
    scenes: audioResult.scenes,
  };
  await generateComposition(compDir, compositionData);
  console.log(`✓ Composition synthesized at: ${compDir}\n`);

  // Step 3: Render, Mux, Verify & Package
  console.log(`[Step 3/3] Rendering and Packaging Verified Short...`);
  const finalResult = await renderAndMux(projectDir, compositionData);

  console.log(`\n🎉 DELIVERABLE COMPLETED SUCCESSFULLY!`);
  console.log(`   📹 Video:     ${finalResult.finalMp4}`);
  console.log(`   🖼️ Cover:     ${finalResult.coverPng}`);
  console.log(`   📋 YouTube SEO: ${path.join(projectDir, "exports", "youtube-package.json")}\n`);
}

main().catch((err) => {
  console.error(`\n❌ Pipeline Error:`, err);
  process.exit(1);
});
