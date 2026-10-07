import React from 'react';
import {AbsoluteFill} from 'remotion';
import type {ThemeProps} from '../runtime/props';

export interface ActionLayerProps {
  sceneId: string;
  subject?: string;
  visualPurpose?: string;
  progress: number;
  width: number;
  height: number;
  theme: ThemeProps;
  isAITopic?: boolean;
}

/**
 * ActionLayer: Renders active, fluid procedural vector blueprint & motion graphics.
 * System-level pipeline implementation supporting both Physical Robotics / Automation
 * and Software / AI Terminology topics with rich environmental anchors, 3D perspective,
 * high mobile readability, and non-redundant callouts.
 */
export const ActionLayer: React.FC<ActionLayerProps> = ({
  sceneId,
  subject = '',
  visualPurpose = '',
  progress,
  width,
  height,
  theme,
  isAITopic = false,
}) => {
  const p = Math.max(0, Math.min(1, progress));
  const accent = theme.accent || '#D97736';
  const sc = sceneId.toLowerCase();
  const sub = subject.toLowerCase();
  const vis = visualPurpose.toLowerCase();

  const isOutro =
    sc.includes('scene_05') ||
    sc.includes('sec_05') ||
    sub.includes('cta') ||
    sub.includes('outro') ||
    sub.includes('subscribe') ||
    sc.includes('brand');

  const isNLPTerms =
    sub.includes('token') ||
    sub.includes('embedding') ||
    sub.includes('attention') ||
    sub.includes('transformer') ||
    sub.includes('vocab') ||
    vis.includes('token') ||
    vis.includes('embedding') ||
    vis.includes('attention') ||
    vis.includes('transformer') ||
    vis.includes('prompt');

  const isRobotics =
    sub.includes('robot') ||
    sub.includes('clamp') ||
    sub.includes('manipulat') ||
    sub.includes('arm') ||
    sub.includes('kinematic') ||
    sub.includes('actuator') ||
    sub.includes('warehouse') ||
    sub.includes('agv') ||
    sub.includes('rover') ||
    vis.includes('robot') ||
    vis.includes('clamp') ||
    vis.includes('arm') ||
    vis.includes('agv');

  const isEnterpriseFDE = !isNLPTerms && !isRobotics;

  // ===========================================================================
  // DOMAIN C: FORWARD DEPLOYED ENGINEER & ENTERPRISE AI SYSTEMS PIPELINE
  // (Architecture Bridge, High-Throughput Data Pipeline, Multi-Agent Orchestration, Production Dashboard)
  // ===========================================================================
  if (isEnterpriseFDE && !isOutro) {
    const cx = width / 2;

    // -------------------------------------------------------------------------
    // FDE SCENE 01: ARCHITECTURE BRIDGE & ENTERPRISE GATEWAY
    // -------------------------------------------------------------------------
    if (sc.includes('scene_01') || sc.includes('sec_01') || sub.includes('hook') || sub.includes('bridge') || sub.includes('fde')) {
      const cardScale = 0.96 + 0.04 * Math.min(1, p * 3.5);
      const pulseT = (p * 4) % 1;

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="fdeCardShadow" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="14" floodColor="#000000" floodOpacity="0.06" />
              </filter>
              <filter id="fdeGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Architectural Blueprint Grid Lines */}
            <line x1={80} y1={420} x2={width - 80} y2={420} stroke="#E2E8F0" strokeWidth={1} strokeDasharray="6 6" opacity={0.6} />
            <line x1={80} y1={1200} x2={width - 80} y2={1200} stroke="#E2E8F0" strokeWidth={1} strokeDasharray="6 6" opacity={0.6} />

            {/* Header Zone: Technical State Tag */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-280} y={-24} width={560} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#fdeCardShadow)" />
              <circle cx={-250} cy={0} r={6} fill="#1E40AF" />
              <text x={-230} y={6} fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                ENTERPRISE ARCHITECTURE // FORWARD DEPLOYED ENGINEER
              </text>
            </g>

            {/* Hero Visualization (Middle Zone): The FDE Production Bridge */}
            <g transform={`translate(${cx}, 680) scale(${cardScale})`}>
              <rect x={-480} y={-180} width={960} height={360} rx={22} fill="#FFFFFF" stroke="#E2E8F0" strokeWidth={2} filter="url(#fdeCardShadow)" />
              <rect x={-480} y={-180} width={960} height={46} rx={22} fill="#F8FAFC" />
              <line x1={-480} y1={-134} x2={480} y2={-134} stroke="#E2E8F0" strokeWidth={1} />
              <circle cx={-445} cy={-157} r={6} fill="#EF4444" />
              <circle cx={-425} cy={-157} r={6} fill="#F59E0B" />
              <circle cx={-405} cy={-157} r={6} fill="#10B981" />
              <text x={-375} y={-152} fill="#64748B" fontSize={13} fontFamily="monospace" fontWeight={700}>
                enterprise_gateway.topology [LIVE PRODUCTION]
              </text>
              <text x={440} y={-152} textAnchor="end" fill="#1E40AF" fontSize={12} fontFamily="monospace" fontWeight={800}>
                STATUS: DEPLOYED
              </text>

              {/* Left Column: Client Infrastructure Stack */}
              <g transform="translate(-320, 20)">
                <rect x={-130} y={-90} width={260} height={180} rx={16} fill="#EFF6FF" stroke="#1E40AF" strokeWidth={2} />
                <rect x={-110} y={-75} width={220} height={28} rx={6} fill="#1E40AF" />
                <text x={0} y={-56} textAnchor="middle" fill="#FFFFFF" fontSize={12} fontFamily="monospace" fontWeight={800}>
                  CLIENT ENTERPRISE STACK
                </text>
                <text x={0} y={-10} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={700}>
                  • Enterprise ERP / SAP
                </text>
                <text x={0} y={16} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={700}>
                  • Production SQL / S3
                </text>
                <text x={0} y={42} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={700}>
                  • Custom Internal APIs
                </text>
                <text x={0} y={70} textAnchor="middle" fill="#64748B" fontSize={11} fontFamily="monospace" fontWeight={600}>
                  [MESSY UNSTRUCTURED DATA]
                </text>
              </g>

              {/* Right Column: Frontier AI Model Core */}
              <g transform="translate(320, 20)">
                <rect x={-130} y={-90} width={260} height={180} rx={16} fill="#FFFBEB" stroke="#D97706" strokeWidth={2} />
                <rect x={-110} y={-75} width={220} height={28} rx={6} fill="#D97706" />
                <text x={0} y={-56} textAnchor="middle" fill="#FFFFFF" fontSize={12} fontFamily="monospace" fontWeight={800}>
                  FRONTIER AI MODEL CORE
                </text>
                <text x={0} y={-10} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={700}>
                  • LLM Weights / API
                </text>
                <text x={0} y={16} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={700}>
                  • Reasoning Engine
                </text>
                <text x={0} y={42} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={700}>
                  • Context Window (2M)
                </text>
                <text x={0} y={70} textAnchor="middle" fill="#D97706" fontSize={11} fontFamily="monospace" fontWeight={600}>
                  [ISOLATED RAW CAPABILITY]
                </text>
              </g>

              {/* Center Conduit: The FDE Integration Gateway */}
              <g transform="translate(0, 20)">
                <line x1={-190} y1={-20} x2={190} y2={-20} stroke="#1E40AF" strokeWidth={3} strokeDasharray="8 6" />
                <line x1={-190} y1={20} x2={190} y2={20} stroke="#D97706" strokeWidth={3} strokeDasharray="8 6" />

                <circle cx={-190 + pulseT * 380} cy={-20} r={6} fill="#1E40AF" filter="url(#fdeGlow)" />
                <circle cx={190 - pulseT * 380} cy={20} r={6} fill="#D97706" filter="url(#fdeGlow)" />

                <rect x={-105} y={-45} width={210} height={90} rx={16} fill="#FFFFFF" stroke="#0F172A" strokeWidth={2.5} filter="url(#fdeCardShadow)" />
                <text x={0} y={-16} textAnchor="middle" fill="#1E40AF" fontSize={12} fontFamily="monospace" fontWeight={900}>
                  ⚡ FORWARD DEPLOYED
                </text>
                <text x={0} y={8} textAnchor="middle" fill="#0F172A" fontSize={16} fontFamily="monospace" fontWeight={900}>
                  ENGINEER
                </text>
                <text x={0} y={28} textAnchor="middle" fill="#64748B" fontSize={11} fontFamily="monospace" fontWeight={700}>
                  LATENCY: 14ms // ACTIVE
                </text>
              </g>
            </g>

            {/* Lower Diagnostic Chips */}
            <g transform={`translate(${cx}, 970)`}>
              <text x={0} y={-40} textAnchor="middle" fill="#64748B" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                THE MISSION: EMBED DIRECTLY & INTEGRATE INTO PRODUCTION
              </text>
              {[
                {label: 'SECURITY: TLS 1.3 / VPC PEERED', x: -280, color: '#1E40AF', bg: '#EFF6FF'},
                {label: 'SCHEMA: DYNAMIC ETL ADAPTATION', x: 0, color: '#0F172A', bg: '#F1F5F9'},
                {label: 'RUNTIME: CLIENT-SITE ZERO-TOUCH', x: 280, color: '#D97706', bg: '#FEF3C7'},
              ].map((chip, idx) => (
                <g key={`chip-${idx}`} transform={`translate(${chip.x}, 0)`}>
                  <rect x={-130} y={-24} width={260} height={48} rx={12} fill={chip.bg} stroke={chip.color} strokeWidth={1.5} filter="url(#fdeCardShadow)" />
                  <text x={0} y={6} textAnchor="middle" fill={chip.color} fontSize={11} fontFamily="monospace" fontWeight={800}>
                    {chip.label}
                  </text>
                </g>
              ))}
            </g>

            {/* Bottom Architecture Banner */}
            <g transform={`translate(${cx}, 1160)`}>
              <line x1={-320} y1={0} x2={320} y2={0} stroke="#E2E8F0" strokeWidth={2} strokeDasharray="8 6" />
              <rect x={-240} y={20} width={480} height={46} rx={12} fill="#FFFFFF" stroke="#1E40AF" strokeWidth={1.5} filter="url(#fdeCardShadow)" />
              <text x={0} y={48} textAnchor="middle" fill="#1E40AF" fontSize={14} fontFamily="monospace" fontWeight={800}>
                BRIDGING THE CHASM TO PRODUCTION DEPLOYMENT ↓
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }

    // -------------------------------------------------------------------------
    // FDE SCENE 02: HIGH-THROUGHPUT DATA PIPELINE & CONTEXT ENGINE
    // -------------------------------------------------------------------------
    if (sc.includes('scene_02') || sc.includes('sec_02') || sub.includes('data') || sub.includes('pipeline') || sub.includes('ingest')) {
      const streams = [
        {title: 'UNSTRUCTURED REPOS', format: 'PDF / DOCS / GIT', badge: '1.4M TOKENS/S', color: '#1E40AF', x: -300},
        {title: 'ENTERPRISE SQL DWH', format: 'POSTGRES / SNOWFLAKE', badge: 'NORMALIZED 0.99', color: '#0D9488', x: 0},
        {title: 'TELEMETRY & LOGS', format: 'KAFKA / CLOUDWATCH', badge: 'LATENCY < 8MS', color: '#D97706', x: 300},
      ];
      const streamProgress = (p * 2.5) % 1;

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="fdeCardShadow2" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="14" floodColor="#000000" floodOpacity="0.06" />
              </filter>
            </defs>

            {/* Header Zone */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-280} y={-24} width={560} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#fdeCardShadow2)" />
              <circle cx={-250} cy={0} r={6} fill="#1E40AF" />
              <text x={-230} y={6} fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                DATA PIPELINE // CONTEXT ASSEMBLY ENGINE
              </text>
            </g>

            {/* Top Source Banner */}
            <g transform={`translate(${cx}, 460)`}>
              <rect x={-420} y={-36} width={840} height={72} rx={16} fill="#FFFFFF" stroke="#E2E8F0" strokeWidth={2} filter="url(#fdeCardShadow2)" />
              <text x={0} y={5} textAnchor="middle" fill="#0F172A" fontSize={22} fontFamily="monospace" fontWeight={800}>
                &lt;ENTERPRISE DATA SOURCES&gt; INGESTION STREAM &lt;/&gt;
              </text>
              <text x={0} y={55} textAnchor="middle" fill="#1E40AF" fontSize={13} fontFamily="monospace" fontWeight={800}>
                CONTINUOUS NORMALIZATION & EMBEDDING STREAM ↓
              </text>
            </g>

            {/* 3 Cascading Pipeline Channels */}
            {streams.map((s, idx) => {
              const startX = cx + s.x;
              const startY = 496;
              const endY = 860;
              const packetY = startY + streamProgress * (endY - startY);

              return (
                <g key={`pipe-${idx}`}>
                  <line x1={startX} y1={startY} x2={startX} y2={endY} stroke={s.color} strokeWidth={2.5} strokeDasharray="8 6" opacity={0.65} />
                  <circle cx={startX} cy={packetY} r={6} fill={s.color} />
                  <circle cx={startX} cy={packetY} r={12} fill="none" stroke={s.color} strokeWidth={1.5} opacity={0.5} />

                  <g transform={`translate(${startX}, 720)`}>
                    <rect x={-130} y={-60} width={260} height={120} rx={16} fill="#FFFFFF" stroke={s.color} strokeWidth={2} filter="url(#fdeCardShadow2)" />
                    <text x={0} y={-26} textAnchor="middle" fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={800}>
                      {s.title}
                    </text>
                    <text x={0} y={-4} textAnchor="middle" fill="#64748B" fontSize={11} fontFamily="monospace" fontWeight={700}>
                      {s.format}
                    </text>
                    <rect x={-90} y={15} width={180} height={28} rx={6} fill="#F8FAFC" stroke="#E2E8F0" strokeWidth={1} />
                    <text x={0} y={34} textAnchor="middle" fill={s.color} fontSize={12} fontFamily="monospace" fontWeight={800}>
                      {s.badge}
                    </text>
                  </g>
                </g>
              );
            })}

            {/* Bottom Aggregator Collector Hub */}
            <g transform={`translate(${cx}, 1040)`}>
              <rect x={-420} y={-60} width={840} height={120} rx={18} fill="#EFF6FF" stroke="#1E40AF" strokeWidth={2.5} filter="url(#fdeCardShadow2)" />
              <text x={0} y={-20} textAnchor="middle" fill="#1E40AF" fontSize={15} fontFamily="monospace" fontWeight={900}>
                ⚡ CONTEXT ASSEMBLY BUFFER // ZERO DATA LEAKAGE
              </text>
              <text x={0} y={12} textAnchor="middle" fill="#0F172A" fontSize={22} fontFamily="monospace" fontWeight={800}>
                STRUCTURED PROMPT INJECTION [READY FOR INFERENCE]
              </text>
              <text x={0} y={40} textAnchor="middle" fill="#64748B" fontSize={12} fontFamily="monospace" fontWeight={700}>
                COMPLIANCE: SOC-2 TYPE II // AES-256 GCM ENCRYPTION
              </text>
            </g>

            {/* Bottom HUD Conduit */}
            <g transform={`translate(${cx}, 1240)`}>
              <line x1={-300} y1={0} x2={300} y2={0} stroke="#E2E8F0" strokeWidth={2} />
              <rect x={-200} y={16} width={400} height={44} rx={12} fill="#FFFFFF" stroke="#0D9488" strokeWidth={1.5} filter="url(#fdeCardShadow2)" />
              <text x={0} y={44} textAnchor="middle" fill="#0D9488" fontSize={14} fontFamily="monospace" fontWeight={800}>
                HIGH-THROUGHPUT REAL-TIME CONTEXT STREAM
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }

    // -------------------------------------------------------------------------
    // FDE SCENE 03: MULTI-AGENT ORCHESTRATION & SYSTEM INTEGRATION
    // -------------------------------------------------------------------------
    if (sc.includes('scene_03') || sc.includes('sec_03') || sub.includes('agent') || sub.includes('orchestrat') || sub.includes('tool')) {
      const nodes = [
        {id: 'gw', title: 'CLIENT API GATEWAY', role: 'SECURITY & ROUTING', x: cx, y: 550, color: '#1E40AF'},
        {id: 'ag1', title: 'REASONING AGENT', role: 'CHAIN-OF-THOUGHT', x: cx - 280, y: 780, color: '#D97706'},
        {id: 'rag', title: 'RAG & VECTOR STORE', role: 'HIGH-DENSITY RETRIEVAL', x: cx + 280, y: 780, color: '#0D9488'},
        {id: 'tool', title: 'ENTERPRISE TOOL RUNNER', role: 'SANDBOX EXECUTION', x: cx, y: 1010, color: '#1E40AF'},
      ];

      const dashOffset = -p * 160;

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="fdeCardShadow3" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="14" floodColor="#000000" floodOpacity="0.06" />
              </filter>
            </defs>

            {/* Header Zone */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-280} y={-24} width={560} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#fdeCardShadow3)" />
              <circle cx={-250} cy={0} r={6} fill="#D97706" />
              <text x={-230} y={6} fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                MULTI-AGENT ORCHESTRATION // SYSTEM INTEGRATION
              </text>
            </g>

            {/* Central Diamond Graph Connection Lines */}
            {[
              {from: 0, to: 1},
              {from: 0, to: 2},
              {from: 1, to: 3},
              {from: 2, to: 3},
              {from: 1, to: 2},
            ].map((edge, idx) => {
              const src = nodes[edge.from];
              const tgt = nodes[edge.to];
              return (
                <g key={`edge-${idx}`}>
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke="#1E40AF"
                    strokeWidth={2.5}
                    strokeDasharray="8 6"
                    strokeDashoffset={dashOffset}
                    opacity={0.65}
                  />
                  <circle
                    cx={src.x + (tgt.x - src.x) * ((p * 3 + idx * 0.25) % 1)}
                    cy={src.y + (tgt.y - src.y) * ((p * 3 + idx * 0.25) % 1)}
                    r={5}
                    fill="#D97706"
                  />
                </g>
              );
            })}

            {/* Central Hub */}
            <g transform={`translate(${cx}, 780)`}>
              <circle cx={0} cy={0} r={68 + Math.sin(p * Math.PI * 4) * 6} fill="none" stroke="#D97706" strokeWidth={2} strokeDasharray="6 4" opacity={0.6} />
              <circle cx={0} cy={0} r={52} fill="#FFFFFF" stroke="#1E40AF" strokeWidth={2.5} filter="url(#fdeCardShadow3)" />
              <text x={0} y={-6} textAnchor="middle" fill="#0F172A" fontSize={13} fontFamily="monospace" fontWeight={900}>
                ORCHESTRATOR
              </text>
              <text x={0} y={16} textAnchor="middle" fill="#D97706" fontSize={11} fontFamily="monospace" fontWeight={800}>
                4 AGENTS
              </text>
            </g>

            {/* 4 Agent Nodes */}
            {nodes.map((node, i) => (
              <g key={`agent-${i}`} transform={`translate(${node.x}, ${node.y})`}>
                <rect x={-140} y={-45} width={280} height={90} rx={18} fill="#FFFFFF" stroke={node.color} strokeWidth={2} filter="url(#fdeCardShadow3)" />
                <text x={0} y={-8} textAnchor="middle" fill="#0F172A" fontSize={15} fontFamily="monospace" fontWeight={900}>
                  {node.title}
                </text>
                <text x={0} y={20} textAnchor="middle" fill={node.color} fontSize={11} fontFamily="monospace" fontWeight={800}>
                  {node.role}
                </text>
              </g>
            ))}

            {/* Bottom Telemetry Card */}
            <g transform={`translate(${cx}, 1240)`}>
              <rect x={-300} y={-24} width={600} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#fdeCardShadow3)" />
              <text x={0} y={6} textAnchor="middle" fill="#1E40AF" fontSize={14} fontFamily="monospace" fontWeight={800}>
                BIDIRECTIONAL TOOL CALLS: 128 OPS/SEC // VERIFIED EXECUTION
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }

    // -------------------------------------------------------------------------
    // FDE SCENE 04: ENTERPRISE BUSINESS IMPACT & CLOUD DASHBOARD
    // -------------------------------------------------------------------------
    if (sc.includes('scene_04') || sc.includes('sec_04') || sub.includes('impact') || sub.includes('value') || sub.includes('scale')) {
      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="fdeCardShadow4" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="14" floodColor="#000000" floodOpacity="0.06" />
              </filter>
            </defs>

            {/* Header Zone */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-280} y={-24} width={560} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#fdeCardShadow4)" />
              <circle cx={-250} cy={0} r={6} fill="#1E40AF" />
              <text x={-230} y={6} fill="#0F172A" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                ENTERPRISE BUSINESS IMPACT // PRODUCTION VALUE
              </text>
            </g>

            {/* 3 Metric Cards */}
            <g transform={`translate(${cx}, 520)`}>
              <rect x={-420} y={-65} width={840} height={130} rx={20} fill="#FFFFFF" stroke="#1E40AF" strokeWidth={2} filter="url(#fdeCardShadow4)" />
              <text x={-380} y={-18} fill="#64748B" fontSize={14} fontFamily="monospace" fontWeight={800}>
                DEPLOYMENT TIMELINE (TIME-TO-VALUE)
              </text>
              <text x={-380} y={32} fill="#1E40AF" fontSize={42} fontFamily="monospace" fontWeight={900}>
                2 WEEKS
              </text>
              <rect x={240} y={-12} width={150} height={40} rx={10} fill="#EFF6FF" stroke="#1E40AF" strokeWidth={1.5} />
              <text x={315} y={14} textAnchor="middle" fill="#1E40AF" fontSize={14} fontFamily="monospace" fontWeight={800}>
                vs 6 MONTHS
              </text>
            </g>

            <g transform={`translate(${cx}, 700)`}>
              <rect x={-420} y={-65} width={840} height={130} rx={20} fill="#FFFFFF" stroke="#0D9488" strokeWidth={2} filter="url(#fdeCardShadow4)" />
              <text x={-380} y={-18} fill="#64748B" fontSize={14} fontFamily="monospace" fontWeight={800}>
                PRODUCTION SYSTEM RELIABILITY
              </text>
              <text x={-380} y={32} fill="#0D9488" fontSize={42} fontFamily="monospace" fontWeight={900}>
                99.99% UPTIME
              </text>
              <rect x={240} y={-12} width={150} height={40} rx={10} fill="#F0FDF4" stroke="#0D9488" strokeWidth={1.5} />
              <text x={315} y={14} textAnchor="middle" fill="#0D9488" fontSize={14} fontFamily="monospace" fontWeight={800}>
                ACTIVE SLA
              </text>
            </g>

            <g transform={`translate(${cx}, 880)`}>
              <rect x={-420} y={-65} width={840} height={130} rx={20} fill="#FFFFFF" stroke="#D97706" strokeWidth={2} filter="url(#fdeCardShadow4)" />
              <text x={-380} y={-18} fill="#64748B" fontSize={14} fontFamily="monospace" fontWeight={800}>
                DEVELOPMENT & CONTEXT VELOCITY
              </text>
              <text x={-380} y={32} fill="#D97706" fontSize={42} fontFamily="monospace" fontWeight={900}>
                +340% GAIN
              </text>
              <rect x={240} y={-12} width={150} height={40} rx={10} fill="#FFFBEB" stroke="#D97706" strokeWidth={1.5} />
              <text x={315} y={14} textAnchor="middle" fill="#D97706" fontSize={14} fontFamily="monospace" fontWeight={800}>
                VERIFIED ROI
              </text>
            </g>

            {/* Cloud Grid at Bottom */}
            <g transform={`translate(${cx}, 1120)`}>
              <line x1={-420} y1={0} x2={420} y2={0} stroke="#E2E8F0" strokeWidth={2} />
              {[-320, -160, 0, 160, 320].map((gx, idx) => (
                <line key={`cloud-grid-${idx}`} x1={gx * 0.5} y1={0} x2={gx} y2={100} stroke="#E2E8F0" strokeWidth={1.5} strokeDasharray="4 4" />
              ))}
              <rect x={-260} y={35} width={520} height={46} rx={12} fill="#FFFFFF" stroke="#1E40AF" strokeWidth={1.5} filter="url(#fdeCardShadow4)" />
              <text x={0} y={64} textAnchor="middle" fill="#1E40AF" fontSize={14} fontFamily="monospace" fontWeight={800}>
                ENTERPRISE SCALE DEPLOYED // MISSION CRITICAL STATUS
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }
  }

  // ===========================================================================
  // DOMAIN A: AI TERMINOLOGY VISUAL PIPELINE
  // (Prompt Ingestion, Token Cascade, Self-Attention Graph, 3D Vector Manifold)
  // ===========================================================================
  if (isNLPTerms && !isOutro) {
    const cx = width / 2;

    // -------------------------------------------------------------------------
    // AI SCENE 01 (00:00 - 00:02): HOOK
    // Sleek macOS/browser-style window card in pure white (#FFFFFF) sitting on the
    // warm cream canvas, featuring a glowing amber cursor typing out the query in
    // Charcoal Black (#1A1917). Active words shatter into crisp white chips with
    // warm amber highlights.
    // -------------------------------------------------------------------------
    if (sc.includes('scene_01') || sc.includes('sec_01') || sub.includes('hook') || sub.includes('prompt')) {
      const promptFull = 'How AI understands human language';
      const typeProgress = Math.min(1, p * 1.5);
      const charsVisible = Math.max(1, Math.floor(typeProgress * promptFull.length));
      const displayedText = promptFull.slice(0, charsVisible);
      const showCursor = Math.floor(p * 20) % 2 === 0;

      const words = [
        {text: 'How', w: 105},
        {text: 'AI', w: 80},
        {text: 'understands', w: 240},
        {text: 'human', w: 135},
        {text: 'language', w: 185},
      ];
      const shatterProgress = Math.max(0, (p - 0.35) / 0.65);
      const scanX = 140 + p * 800;
      const cardScale = 0.96 + 0.04 * Math.min(1, p * 3.5);

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="claudeCardShadow" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="12" floodColor="#000000" floodOpacity="0.06" />
              </filter>
              <filter id="softAmberGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Fine Engineering Blueprint Grid Overlay (#E2E8F0, 40% Opacity) */}
            <line x1={80} y1={420} x2={width - 80} y2={420} stroke="#E2E8F0" strokeWidth={1} strokeDasharray="6 6" opacity={0.6} />
            <line x1={80} y1={1200} x2={width - 80} y2={1200} stroke="#E2E8F0" strokeWidth={1} strokeDasharray="6 6" opacity={0.6} />

            {/* Header Zone (Top 15%): Technical Pipeline State Tag */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-260} y={-24} width={520} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow)" />
              <circle cx={-230} cy={0} r={6} fill="#D97706" />
              <text x={-210} y={6} fill="#1A1917" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                PROMPT INGESTION // STEP 01
              </text>
            </g>

            {/* Hero Graphic Zone (Middle 60%): Sleek macOS/Browser Card in Pure White */}
            <g transform={`translate(${cx}, 620) scale(${cardScale})`}>
              {/* Card Container with Soft Drop Shadow */}
              <rect
                x={-460}
                y={-140}
                width={920}
                height={260}
                rx={20}
                fill="#FFFFFF"
                stroke="#E5E7EB"
                strokeWidth={2}
                filter="url(#claudeCardShadow)"
              />
              
              {/* Window Header Bar with macOS dots */}
              <rect x={-460} y={-140} width={920} height={46} rx={20} fill="#F8FAFC" />
              <rect x={-460} y={-100} width={920} height={6} fill="#F8FAFC" />
              <line x1={-460} y1={-94} x2={460} y2={-94} stroke="#E5E7EB" strokeWidth={1} />
              <circle cx={-425} cy={-117} r={6} fill="#EF4444" />
              <circle cx={-405} cy={-117} r={6} fill="#F59E0B" />
              <circle cx={-385} cy={-117} r={6} fill="#10B981" />
              <text x={-355} y={-112} fill="#64748B" fontSize={13} fontFamily="monospace" fontWeight={700}>
                natural_language_query.prompt [UTF-8]
              </text>
              <text x={430} y={-112} textAnchor="end" fill="#94A3B8" fontSize={12} fontFamily="monospace" fontWeight={600}>
                PROMPT STREAM
              </text>

              {/* Glowing Amber Prompt Command Symbol */}
              <text x={-420} y={2} fill="#D97706" fontSize={38} fontFamily="monospace" fontWeight={900}>
                &gt;
              </text>

              {/* High-Contrast Charcoal Black Typed Text */}
              <text x={-380} y={0} fill="#1A1917" fontSize={34} fontFamily="monospace" fontWeight={800}>
                {displayedText}
                {showCursor ? <tspan fill="#D97706">|</tspan> : null}
              </text>

              {/* Window Sub-status Guide */}
              <line x1={-420} y1={52} x2={420} y2={52} stroke="#E2E8F0" strokeWidth={1} strokeDasharray="4 4" />
              <text x={-420} y={85} fill="#64748B" fontSize={14} fontFamily="monospace" fontWeight={600}>
                STATUS: RECEIVING RAW USER INPUT...
              </text>
              <text x={420} y={85} textAnchor="end" fill="#D97706" fontSize={14} fontFamily="monospace" fontWeight={800}>
                {charsVisible}/{promptFull.length} CHARS
              </text>
            </g>

            {/* Word Boundary Decomposition: Clean White Chips with Amber Highlight */}
            <g transform={`translate(${cx}, 930)`}>
              {/* Section Subtitle */}
              <text x={0} y={-50} textAnchor="middle" fill="#64748B" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.1em">
                IDENTIFYING LEXICAL BOUNDARIES // WORD DECOMPOSITION
              </text>

              {/* Laser Scanner Line in Amber */}
              <line x1={scanX - cx} y1={-32} x2={scanX - cx} y2={74} stroke="#D97706" strokeWidth={2.5} filter="url(#softAmberGlow)" />

              {/* Exploded Word Chips */}
              {words.map((w, i) => {
                const totalW = words.reduce((acc, item) => acc + item.w + 18, -18);
                let startX = -totalW / 2;
                for (let k = 0; k < i; k++) {
                  startX += words[k].w + 18;
                }
                const chipX = startX + w.w / 2 + (i - 2) * shatterProgress * 20;
                const chipY = Math.sin(p * Math.PI * 2 + i) * 6;
                const isHighlighted = p > 0.2 + i * 0.12;

                return (
                  <g key={`word-${i}`} transform={`translate(${chipX}, ${chipY})`}>
                    <rect
                      x={-w.w / 2}
                      y={-30}
                      width={w.w}
                      height={60}
                      rx={14}
                      fill={isHighlighted ? '#FEF3C7' : '#FFFFFF'}
                      stroke={isHighlighted ? '#D97706' : '#E5E7EB'}
                      strokeWidth={isHighlighted ? 2.5 : 1.5}
                      filter="url(#claudeCardShadow)"
                    />
                    <text
                      x={0}
                      y={8}
                      textAnchor="middle"
                      fill={isHighlighted ? '#92400E' : '#1A1917'}
                      fontSize={21}
                      fontFamily="monospace"
                      fontWeight={900}
                    >
                      {w.text}
                    </text>
                  </g>
                );
              })}
            </g>

            {/* Bottom Pipeline Conduit */}
            <g transform={`translate(${cx}, 1150)`}>
              <line x1={-300} y1={0} x2={300} y2={0} stroke="#E2E8F0" strokeWidth={2} strokeDasharray="8 6" />
              <rect x={-190} y={20} width={380} height={44} rx={12} fill="#FFFFFF" stroke="#2563EB" strokeWidth={1.5} filter="url(#claudeCardShadow)" />
              <text x={0} y={48} textAnchor="middle" fill="#2563EB" fontSize={14} fontFamily="monospace" fontWeight={800}>
                READY FOR NUMERICAL TOKENIZATION ↓
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }

    // -------------------------------------------------------------------------
    // AI SCENE 02 (00:03 - 00:09): TOKENIZATION
    // Crisp white token cards floating above a light gray vector matrix grid.
    // Token IDs ([2044], #99301, [124], [4512]) render in Cobalt Blue (#2563EB)
    // inside small neutral-gray pills (#F1F5F9).
    // -------------------------------------------------------------------------
    if (sc.includes('scene_02') || sc.includes('sec_02') || (!sc.includes('scene_01') && !sc.includes('scene_03') && !sc.includes('scene_04') && !sc.includes('scene_05') && sub.includes('token'))) {
      const tokens = [
        {word: 'How', id: '[2044]', hexId: '0x07FC', targetX: 200, targetY: 960},
        {word: 'AI', id: '#99301', hexId: '0x183E', targetX: 420, targetY: 920},
        {word: 'understands', id: '[124]', hexId: '0x007C', targetX: 660, targetY: 920},
        {word: 'language', id: '[4512]', hexId: '0x11A0', targetX: 880, targetY: 960},
      ];

      const cascadeProgress = Math.min(1, p * 1.3);

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="claudeCardShadow2" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="12" floodColor="#000000" floodOpacity="0.06" />
              </filter>
            </defs>

            {/* Header Zone: Technical State Tag */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-260} y={-24} width={520} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow2)" />
              <circle cx={-230} cy={0} r={6} fill="#2563EB" />
              <text x={-210} y={6} fill="#1A1917" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                TOKENIZATION PIPELINE // STEP 02
              </text>
            </g>

            {/* Top Source String Container (Pure White Card) */}
            <g transform={`translate(${cx}, 470)`}>
              <rect x={-380} y={-36} width={760} height={72} rx={16} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={2} filter="url(#claudeCardShadow2)" />
              <text x={0} y={6} textAnchor="middle" fill="#1A1917" fontSize={24} fontFamily="monospace" fontWeight={800}>
                &lt;STREAM&gt; "How AI understands language" &lt;/STREAM&gt;
              </text>
              <text x={0} y={56} textAnchor="middle" fill="#2563EB" fontSize={13} fontFamily="monospace" fontWeight={800}>
                CONVERTING TO DISCRETE VOCABULARY INDICES ↓
              </text>
            </g>

            {/* Downward Cascading Motion Trails (Cobalt & Amber) */}
            {tokens.map((t, i) => {
              const startX = 260 + i * 180;
              const startY = 506;
              const curX = startX + (t.targetX - startX) * cascadeProgress;
              const curY = startY + (t.targetY - startY) * cascadeProgress;

              return (
                <g key={`trail-${i}`}>
                  <line
                    x1={startX}
                    y1={startY}
                    x2={curX}
                    y2={curY}
                    stroke={i % 2 === 0 ? '#1E40AF' : '#D97706'}
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    opacity={0.65}
                  />
                  {/* Rule B: Dynamic Data Flow Pulse Particle */}
                  <circle
                    cx={startX + (curX - startX) * ((p * 3 + i * 0.25) % 1)}
                    cy={startY + (curY - startY) * ((p * 3 + i * 0.25) % 1)}
                    r={4}
                    fill={i % 2 === 0 ? '#1E40AF' : '#D97706'}
                  />
                  <circle cx={curX} cy={curY - 30} r={3} fill={i % 2 === 0 ? '#1E40AF' : '#D97706'} opacity={0.8} />
                </g>
              );
            })}

            {/* Cascading Crisp White Token Cards (+30% Scaled for Mobile Readability) */}
            {tokens.map((t, i) => {
              const startX = 260 + i * 180;
              const startY = 506;
              const curX = startX + (t.targetX - startX) * cascadeProgress;
              const curY = startY + (t.targetY - startY) * cascadeProgress + Math.sin(p * Math.PI * 3 + i) * 8;

              return (
                <g key={`tok-${i}`} transform={`translate(${curX}, ${curY})`}>
                  {/* Outer Crisp White Card */}
                  <rect
                    x={-100}
                    y={-55}
                    width={200}
                    height={110}
                    rx={18}
                    fill="#FFFFFF"
                    stroke="#E5E7EB"
                    strokeWidth={2}
                    filter="url(#claudeCardShadow2)"
                  />
                  {/* Word Header */}
                  <text x={0} y={-24} textAnchor="middle" fill="#1A1917" fontSize={18} fontFamily="monospace" fontWeight={800}>
                    "{t.word}"
                  </text>
                  {/* Neutral-Gray Pill housing Cobalt Blue Token ID */}
                  <rect x={-65} y={-3} width={130} height={34} rx={8} fill="#F1F5F9" stroke="#E2E8F0" strokeWidth={1} />
                  <text x={0} y={21} textAnchor="middle" fill="#2563EB" fontSize={22} fontFamily="monospace" fontWeight={900}>
                    {t.id}
                  </text>
                  {/* Metadata Sub-annotation */}
                  <text x={0} y={44} textAnchor="middle" fill="#64748B" fontSize={11} fontFamily="monospace" fontWeight={700}>
                    VOCAB_IDX // {t.hexId}
                  </text>
                </g>
              );
            })}

            {/* 3D Matrix Coordinate Grid at Bottom (Light Slate Blueprint Lines) */}
            <g transform={`translate(${cx}, 1200)`}>
              {/* Perspective Horizon Line */}
              <line x1={-440} y1={0} x2={440} y2={0} stroke="#E2E8F0" strokeWidth={2} />
              
              {/* Matrix Grid Perspective Lines */}
              {[-360, -180, 0, 180, 360].map((gx, idx) => (
                <line
                  key={`mat-grid-${idx}`}
                  x1={gx * 0.4}
                  y1={0}
                  x2={gx}
                  y2={220}
                  stroke="#E2E8F0"
                  strokeWidth={1.5}
                  strokeDasharray="4 4"
                />
              ))}

              {/* Horizontal Matrix Depth Rungs */}
              {[60, 130, 200].map((ry, idx) => (
                <line
                  key={`mat-rung-${idx}`}
                  x1={-360 * (0.4 + idx * 0.25)}
                  y1={ry}
                  x2={360 * (0.4 + idx * 0.25)}
                  y2={ry}
                  stroke="#E2E8F0"
                  strokeWidth={1.5}
                />
              ))}

              {/* Coordinate Space Slot Indicators */}
              {tokens.map((t, i) => {
                const slotX = -270 + i * 180;
                return (
                  <g key={`slot-${i}`} transform={`translate(${slotX}, 130)`}>
                    <ellipse cx={0} cy={0} rx={75} ry={24} fill="#FFFFFF" stroke="#2563EB" strokeWidth={1.5} strokeDasharray="4 4" />
                    <text x={0} y={38} textAnchor="middle" fill="#2563EB" fontSize={13} fontFamily="monospace" fontWeight={800}>
                      SLOT #{i} [DIM: 768]
                    </text>
                  </g>
                );
              })}

              {/* Tensor Spec Card */}
              <g transform="translate(0, 230)">
                <rect x={-260} y={-22} width={520} height={44} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow2)" />
                <text x={0} y={6} textAnchor="middle" fill="#2563EB" fontSize={15} fontFamily="monospace" fontWeight={800}>
                  TENSOR SHAPE: [1, 4, 768] // DENSE VECTOR MATRIX
                </text>
              </g>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }

    // -------------------------------------------------------------------------
    // AI SCENE 03 (00:10 - 00:16): ATTENTION WEIGHT GRAPH
    // Word nodes represented as clean white badges with charcoal text (#1A1917).
    // Attention lines animate as Terracotta/Amber (#D97706) vector arcs with
    // subtle weight values hovering along the lines.
    // -------------------------------------------------------------------------
    if (sc.includes('scene_03') || sc.includes('sec_03') || (!sc.includes('scene_01') && !sc.includes('scene_02') && !sc.includes('scene_04') && !sc.includes('scene_05') && sub.includes('attention'))) {
      const nodes = [
        {id: 'ai', text: 'AI', x: 260, y: 720, color: '#D97706'},
        {id: 'understands', text: 'understands', x: 820, y: 720, color: '#2563EB'},
        {id: 'human', text: 'human', x: 260, y: 1140, color: '#0D9488'},
        {id: 'language', text: 'language', x: 820, y: 1140, color: '#D97706'},
      ];

      // Attention connection weights
      const edges = [
        {from: 0, to: 3, weight: 0.94, label: 'α=0.94 [KEY DEPENDENCY]', color: '#D97706', width: 6.5},
        {from: 1, to: 3, weight: 0.82, label: 'α=0.82', color: '#2563EB', width: 4.5},
        {from: 2, to: 3, weight: 0.74, label: 'α=0.74', color: '#0D9488', width: 3.5},
        {from: 0, to: 1, weight: 0.45, label: 'α=0.45', color: '#94A3B8', width: 2},
        {from: 0, to: 2, weight: 0.28, label: 'α=0.28', color: '#CBD5E1', width: 1.5},
        {from: 1, to: 2, weight: 0.32, label: 'α=0.32', color: '#CBD5E1', width: 1.5},
      ];

      const dashOffset = -p * 180;

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="claudeCardShadow3" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="12" floodColor="#000000" floodOpacity="0.06" />
              </filter>
            </defs>

            {/* Header Zone: Technical State Tag */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-260} y={-24} width={520} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow3)" />
              <circle cx={-230} cy={0} r={6} fill="#D97706" />
              <text x={-210} y={6} fill="#1A1917" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                MULTI-HEAD SELF-ATTENTION // 8 HEADS
              </text>
            </g>

            {/* Formula Banner (Clean White Card) */}
            <g transform={`translate(${cx}, 440)`}>
              <rect x={-340} y={-32} width={680} height={64} rx={16} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow3)" />
              <text x={0} y={8} textAnchor="middle" fill="#1A1917" fontSize={19} fontFamily="monospace" fontWeight={800}>
                Attention(Q, K, V) = softmax(Q K^T / √d_k) · V
              </text>
            </g>

            {/* Central Attention Mechanism Core Hub */}
            <g transform={`translate(${cx}, 930)`}>
              <circle cx={0} cy={0} r={72 + Math.sin(p * Math.PI * 4) * 6} fill="none" stroke="#D97706" strokeWidth={2} strokeDasharray="6 4" opacity={0.6} />
              <circle cx={0} cy={0} r={56} fill="#FFFFFF" stroke="#D97706" strokeWidth={2.5} filter="url(#claudeCardShadow3)" />
              <text x={0} y={-6} textAnchor="middle" fill="#1A1917" fontSize={14} fontFamily="monospace" fontWeight={900}>
                ATTENTION
              </text>
              <text x={0} y={16} textAnchor="middle" fill="#D97706" fontSize={12} fontFamily="monospace" fontWeight={800}>
                HEAD #1
              </text>
            </g>

            {/* Dynamic Attention Weight Connection Lines (Line-drawing with strokeDashoffset) */}
            {edges.map((e, idx) => {
              const src = nodes[e.from];
              const tgt = nodes[e.to];
              const isPrimary = e.weight > 0.8;

              return (
                <g key={`edge-${idx}`}>
                  {/* Main Electrical Conduit Line */}
                  <line
                    x1={src.x}
                    y1={src.y}
                    x2={tgt.x}
                    y2={tgt.y}
                    stroke={e.color}
                    strokeWidth={e.width}
                    strokeDasharray={isPrimary ? '12 8' : '6 6'}
                    strokeDashoffset={dashOffset}
                    opacity={isPrimary ? 1 : 0.55}
                  />

                  {/* Rule B: Dynamic Data Flow Pulse Particle */}
                  <circle
                    cx={src.x + (tgt.x - src.x) * ((p * 2.8 + idx * 0.22) % 1)}
                    cy={src.y + (tgt.y - src.y) * ((p * 2.8 + idx * 0.22) % 1)}
                    r={isPrimary ? 5 : 3.5}
                    fill={e.color}
                    filter="url(#claudeCardShadow3)"
                  />

                  {/* Weight Callout Badge for Strong Connections */}
                  {isPrimary ? (
                    <g transform={`translate(${(src.x + tgt.x) / 2}, ${(src.y + tgt.y) / 2})`}>
                      <rect x={-95} y={-16} width={190} height={32} rx={8} fill="#FFFFFF" stroke={e.color} strokeWidth={1.5} filter="url(#claudeCardShadow3)" />
                      <text x={0} y={5} textAnchor="middle" fill={e.color} fontSize={13} fontFamily="monospace" fontWeight={900}>
                        {e.label}
                      </text>
                    </g>
                  ) : null}
                </g>
              );
            })}

            {/* Token Graph Nodes: Clean White Badges with Charcoal Text */}
            {nodes.map((node, i) => {
              const pulse = Math.sin(p * Math.PI * 4 + i) * 5;
              return (
                <g key={`node-${i}`} transform={`translate(${node.x}, ${node.y})`}>
                  {/* Subtle Focus Ring */}
                  <circle cx={0} cy={0} r={62 + pulse} fill="none" stroke={node.color} strokeWidth={1.5} opacity={0.5} />

                  {/* Main Clean White Node Card */}
                  <rect
                    x={-95}
                    y={-45}
                    width={190}
                    height={90}
                    rx={18}
                    fill="#FFFFFF"
                    stroke={node.color}
                    strokeWidth={2}
                    filter="url(#claudeCardShadow3)"
                  />
                  <text x={0} y={-4} textAnchor="middle" fill="#1A1917" fontSize={24} fontFamily="monospace" fontWeight={900}>
                    "{node.text}"
                  </text>
                  <text x={0} y={24} textAnchor="middle" fill={node.color} fontSize={13} fontFamily="monospace" fontWeight={800}>
                    TOKEN #{i} [Q_{i} · K_j]
                  </text>
                </g>
              );
            })}

            {/* Bottom Telemetry Card */}
            <g transform={`translate(${cx}, 1320)`}>
              <rect x={-260} y={-24} width={520} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow3)" />
              <text x={0} y={6} textAnchor="middle" fill="#2563EB" fontSize={14} fontFamily="monospace" fontWeight={800}>
                DYNAMIC ATTENTION WEIGHT MATRIX // 100% CONTEXTUALIZED
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }

    // -------------------------------------------------------------------------
    // AI SCENE 04 (00:17 - 00:23): HIGH-DIMENSIONAL VECTOR SPACE
    // Rotating 3D vector point cloud showing cluster points floating in warm
    // light space with distance vectors connecting semantic neighbors.
    // -------------------------------------------------------------------------
    if (sc.includes('scene_04') || sc.includes('sec_04') || (!sc.includes('scene_01') && !sc.includes('scene_02') && !sc.includes('scene_03') && !sc.includes('scene_05') && (sub.includes('vector') || sub.includes('embedding') || sub.includes('transformer')))) {
      // 3D Orbital Rotation Angles
      const rotY = p * Math.PI * 0.8 - 0.4;
      const rotX = 0.3 + Math.sin(p * Math.PI) * 0.08;
      const cy3D = 920;

      // 3D Point Cloud Definition [x, y, z, label, cluster, color]
      const rawPoints = [
        // Cluster A: Syntax & Representation (Cobalt Blue #2563EB)
        {x: -180, y: -90, z: -40, label: 'token', cluster: 'A', color: '#2563EB'},
        {x: -110, y: -150, z: 30, label: 'vector', cluster: 'A', color: '#2563EB'},
        {x: -220, y: -30, z: 70, label: 'word', cluster: 'A', color: '#2563EB'},
        {x: -150, y: 30, z: -50, label: 'symbol', cluster: 'A', color: '#2563EB'},

        // Cluster B: Semantics & Meaning (Terracotta / Amber #D97706)
        {x: 160, y: -70, z: 50, label: 'meaning', cluster: 'B', color: '#D97706'},
        {x: 210, y: -120, z: -30, label: 'context', cluster: 'B', color: '#D97706'},
        {x: 130, y: 30, z: 80, label: 'attention', cluster: 'B', color: '#D97706'},
        {x: 230, y: 20, z: -40, label: 'concept', cluster: 'B', color: '#D97706'},

        // Cluster C: Neural Parameters (Teal #0D9488)
        {x: 0, y: 130, z: -40, label: 'weights', cluster: 'C', color: '#0D9488'},
        {x: 40, y: 180, z: 40, label: 'matrix', cluster: 'C', color: '#0D9488'},
      ];

      // Perspective 3D Projection
      const focal = 650;
      const camDist = 550;

      const projected = rawPoints.map((pt) => {
        // Rotate around Y
        const x1 = pt.x * Math.cos(rotY) + pt.z * Math.sin(rotY);
        const z1 = -pt.x * Math.sin(rotY) + pt.z * Math.cos(rotY);
        // Rotate around X
        const y1 = pt.y * Math.cos(rotX) - z1 * Math.sin(rotX);
        const z2 = pt.y * Math.sin(rotX) + z1 * Math.cos(rotX);

        const scale = focal / (camDist + z2);
        return {
          ...pt,
          projX: cx + x1 * scale,
          projY: cy3D + y1 * scale,
          scale,
          zDepth: z2,
        };
      });

      // Semantic Neighbor Pairs
      const neighborPairs = [
        {fromIdx: 0, toIdx: 1, dist: 'cos(θ)=0.962', color: '#2563EB'},
        {fromIdx: 4, toIdx: 5, dist: 'cos(θ)=0.941', color: '#D97706'},
        {fromIdx: 6, toIdx: 7, dist: 'cos(θ)=0.895', color: '#D97706'},
        {fromIdx: 8, toIdx: 9, dist: 'cos(θ)=0.912', color: '#0D9488'},
        {fromIdx: 1, toIdx: 4, dist: 'd=0.48 [CROSS]', color: '#94A3B8'},
      ];

      return (
        <AbsoluteFill style={{pointerEvents: 'none'}}>
          <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            <defs>
              <filter id="claudeCardShadow4" x="-15%" y="-15%" width="130%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="12" floodColor="#000000" floodOpacity="0.06" />
              </filter>
            </defs>

            {/* Header Zone: Technical State Tag */}
            <g transform={`translate(${cx}, 320)`}>
              <rect x={-260} y={-24} width={520} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow4)" />
              <circle cx={-230} cy={0} r={6} fill="#2563EB" />
              <text x={-210} y={6} fill="#1A1917" fontSize={14} fontFamily="monospace" fontWeight={800} letterSpacing="0.08em">
                ROTATING 3D SEMANTIC VECTOR SPACE
              </text>
            </g>

            {/* Dimension Readout Sub-card */}
            <g transform={`translate(${cx}, 440)`}>
              <rect x={-280} y={-26} width={560} height={52} rx={14} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow4)" />
              <text x={0} y={6} textAnchor="middle" fill="#64748B" fontSize={15} fontFamily="monospace" fontWeight={800}>
                HIGH-DIMENSIONAL EMBEDDING MANIFOLD [1,536-D]
              </text>
            </g>

            {/* 3D Origin Axes Gimbal (Light Slate Blueprint Guides) */}
            <g transform={`translate(${cx}, ${cy3D})`}>
              <ellipse cx={0} cy={0} rx={280} ry={90} fill="none" stroke="#E2E8F0" strokeWidth={1.5} strokeDasharray="6 6" />
              <ellipse cx={0} cy={0} rx={180} ry={240} fill="none" stroke="#E2E8F0" strokeWidth={1} strokeDasharray="4 6" opacity={0.6} />
              <circle cx={0} cy={0} r={5} fill="#CBD5E1" />
            </g>

            {/* Distance Vectors Connecting Semantic Neighbors */}
            {neighborPairs.map((pair, pIdx) => {
              const p1 = projected[pair.fromIdx];
              const p2 = projected[pair.toIdx];
              const isHighlight = pIdx < 3;

              return (
                <g key={`pair-${pIdx}`}>
                  <line
                    x1={p1.projX}
                    y1={p1.projY}
                    x2={p2.projX}
                    y2={p2.projY}
                    stroke={pair.color}
                    strokeWidth={isHighlight ? 2.5 : 1.5}
                    strokeDasharray={isHighlight ? '6 4' : '3 3'}
                    opacity={isHighlight ? 0.9 : 0.45}
                  />

                  {/* Distance Cosine Callout Badge */}
                  {isHighlight ? (
                    <g transform={`translate(${(p1.projX + p2.projX) / 2}, ${(p1.projY + p2.projY) / 2 - 12})`}>
                      <rect x={-65} y={-14} width={130} height={28} rx={7} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow4)" />
                      <text x={0} y={5} textAnchor="middle" fill={pair.color} fontSize={12} fontFamily="monospace" fontWeight={800}>
                        {pair.dist}
                      </text>
                    </g>
                  ) : null}
                </g>
              );
            })}

            {/* 3D Vector Point Cloud Elements */}
            {projected
              .sort((a, b) => b.zDepth - a.zDepth) // Z-sort for true 3D depth
              .map((pt, i) => {
                const radius = Math.max(5, 9 * pt.scale);

                return (
                  <g key={`pt-${i}`} transform={`translate(${pt.projX}, ${pt.projY})`}>
                    {/* Glowing Vector Point */}
                    <circle cx={0} cy={0} r={radius + 4} fill="none" stroke={pt.color} strokeWidth={1.5} opacity={0.5} />
                    <circle cx={0} cy={0} r={radius} fill={pt.color} />

                    {/* Semantic Label Badge: Clean White Card with Charcoal Text */}
                    <g transform={`translate(0, ${-radius - 22})`}>
                      <rect
                        x={-55 * pt.scale}
                        y={-14 * pt.scale}
                        width={110 * pt.scale}
                        height={28 * pt.scale}
                        rx={6 * pt.scale}
                        fill="#FFFFFF"
                        stroke="#E5E7EB"
                        strokeWidth={1.5}
                        filter="url(#claudeCardShadow4)"
                      />
                      <text
                        x={0}
                        y={4 * pt.scale}
                        textAnchor="middle"
                        fill="#1A1917"
                        fontSize={Math.max(11, 14 * pt.scale)}
                        fontFamily="monospace"
                        fontWeight={900}
                      >
                        "{pt.label}"
                      </text>
                    </g>
                  </g>
                );
              })}

            {/* Bottom HUD Telemetry Card */}
            <g transform={`translate(${cx}, 1320)`}>
              <rect x={-260} y={-24} width={520} height={48} rx={12} fill="#FFFFFF" stroke="#E5E7EB" strokeWidth={1.5} filter="url(#claudeCardShadow4)" />
              <text x={0} y={6} textAnchor="middle" fill="#D97706" fontSize={14} fontFamily="monospace" fontWeight={800}>
                COSINE CLUSTERING // SIMILAR CONCEPTS CONVERGE
              </text>
            </g>
          </svg>
        </AbsoluteFill>
      );
    }
  }

  // ===========================================================================
  // DOMAIN B: PHYSICAL ROBOTICS & WAREHOUSE AUTOMATION PIPELINE
  // (Industrial Manipulator, 3D Kinematics, Aisle Rerouting, 3D AGV Perspective)
  // ===========================================================================
  if (isRobotics && !isOutro) {
    // ---------------------------------------------------------------------------
    // SCENE 01: INDUSTRIAL WAREHOUSE ROBOTIC PICKING ARM & TACTILE CLAMPING
    // ---------------------------------------------------------------------------
    if (sc.includes('scene_01') || sc.includes('sec_01') || sc.includes('clamp') || sc.includes('grip')) {
      const cx = width / 2;

    // Snappier physical cycle (1.35x speed):
    // Phase 1 (p < 0.22): Gantry trolley and arm descend into pick zone
    // Phase 2 (0.22 <= p < 0.50): Rapid cubic clamping onto package
    // Phase 3 (p >= 0.50): Zero-slip verified, gantry lifts payload cleanly
    const descentT = Math.min(1, p / 0.22);
    const liftT = p >= 0.50 ? Math.min(1, (p - 0.50) / 0.50) : 0;
    const armY = 620 + descentT * 130 - liftT * 90; // y: 620 -> 750 -> 660

    const clampT = Math.max(0, Math.min(1, (p - 0.20) / 0.28));
    const easeClamp = clampT < 0.5 ? 4 * clampT * clampT * clampT : 1 - Math.pow(-2 * clampT + 2, 3) / 2;
    const jawGap = 110 * (1 - easeClamp);
    const isClamped = p >= 0.48;

    const forceProgress = isClamped ? Math.min(1, (p - 0.48) / 0.28) : 0;
    const currentForce = (forceProgress * 14.8).toFixed(1);

    // Shockwave pulse upon tactile confirmation
    const pulseT = isClamped ? ((p - 0.48) * 3.5) % 1 : 0;
    const pulseRadius = 35 + pulseT * 95;
    const pulseOpacity = Math.max(0, 0.75 * (1 - pulseT));

    // Non-overlapping Top-Right HUD Card & Angled Leader Line
    const hudX = 760;
    const hudY = 340;
    const contactX = cx + 72 + jawGap;
    const contactY = armY + 70;

    return (
      <AbsoluteFill style={{pointerEvents: 'none'}}>
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id="gantryBeamGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1E293B" />
              <stop offset="50%" stopColor="#334155" />
              <stop offset="100%" stopColor="#0F172A" />
            </linearGradient>
            <linearGradient id="armShaftGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#1E293B" />
              <stop offset="50%" stopColor="#334155" />
              <stop offset="100%" stopColor="#0F172A" />
            </linearGradient>
            <linearGradient id="jawGradLeft" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#1E293B" stopOpacity="0.98" />
              <stop offset="100%" stopColor="#334155" stopOpacity="0.98" />
            </linearGradient>
            <linearGradient id="jawGradRight" x1="1" y1="0" x2="0" y2="0">
              <stop offset="0%" stopColor="#1E293B" stopOpacity="0.98" />
              <stop offset="100%" stopColor="#334155" stopOpacity="0.98" />
            </linearGradient>
            <linearGradient id="payloadGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#1D4ED8" stopOpacity="0.95" />
            </linearGradient>
            <filter id="softGlow1" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 1. ENVIRONMENTAL ANCHOR: High-Bay Warehouse Racking Silhouettes (Flanks) */}
          {/* Left Storage Racks */}
          <g opacity={0.35}>
            <line x1={80} y1={280} x2={80} y2={1240} stroke="#334155" strokeWidth={3} />
            <line x1={180} y1={280} x2={180} y2={1240} stroke="#334155" strokeWidth={3} />
            {[420, 600, 780, 960, 1140].map((ry) => (
              <g key={`lrack-${ry}`}>
                <line x1={80} y1={ry} x2={180} y2={ry} stroke="#475569" strokeWidth={2.5} />
                <rect x={90} y={ry - 55} width={80} height={50} rx={4} fill="#1E293B" stroke="#334155" strokeWidth={1} />
                <line x1={80} y1={ry} x2={180} y2={ry - 90} stroke="#1E293B" strokeWidth={1.5} />
              </g>
            ))}
          </g>
          {/* Right Storage Racks */}
          <g opacity={0.35}>
            <line x1={width - 180} y1={280} x2={width - 180} y2={1240} stroke="#334155" strokeWidth={3} />
            <line x1={width - 80} y1={280} x2={width - 80} y2={1240} stroke="#334155" strokeWidth={3} />
            {[420, 600, 780, 960, 1140].map((ry) => (
              <g key={`rrack-${ry}`}>
                <line x1={width - 180} y1={ry} x2={width - 80} y2={ry} stroke="#475569" strokeWidth={2.5} />
                <rect x={width - 170} y={ry - 55} width={80} height={50} rx={4} fill="#1E293B" stroke="#334155" strokeWidth={1} />
                <line x1={width - 180} y1={ry} x2={width - 80} y2={ry - 90} stroke="#1E293B" strokeWidth={1.5} />
              </g>
            ))}
          </g>

          {/* 2. ENVIRONMENTAL ANCHOR: Overhead Structural Gantry Runway Girder & Hoist Trolley */}
          <g transform="translate(0, 160)">
            <rect x={0} y={0} width={width} height={50} fill="url(#gantryBeamGrad)" stroke="#475569" strokeWidth={2} />
            <line x1={0} y1={12} x2={width} y2={12} stroke="#64748B" strokeWidth={2} />
            <line x1={0} y1={38} x2={width} y2={38} stroke="#1E293B" strokeWidth={2} />
            {[100, 260, 420, 580, 740, 900].map((gx) => (
              <g key={`gant-${gx}`}>
                <line x1={gx} y1={0} x2={gx + 80} y2={50} stroke="#334155" strokeWidth={1.5} opacity={0.5} />
                <line x1={gx + 80} y1={0} x2={gx} y2={50} stroke="#334155" strokeWidth={1.5} opacity={0.5} />
              </g>
            ))}
            <rect x={cx - 100} y={42} width={200} height={36} rx={6} fill="#0F172A" stroke="#94A3B8" strokeWidth={2} />
            <circle cx={cx - 60} cy={50} r={8} fill="#334155" stroke="#94A3B8" strokeWidth={1.5} />
            <circle cx={cx + 60} cy={50} r={8} fill="#334155" stroke="#94A3B8" strokeWidth={1.5} />
            <path d={`M ${cx - 70} 65 C ${cx - 90} 110, ${cx - 60} 140, ${cx - 36} ${armY - 160}`} fill="none" stroke="#F59E0B" strokeWidth={3} strokeDasharray="6 4" opacity={0.8} />
          </g>

          {/* 3. ENVIRONMENTAL ANCHOR: Warehouse Conveyor Table & Motorized Rollers Beneath Payload */}
          <g transform="translate(0, 980)">
            <rect x={180} y={0} width={width - 360} height={28} rx={4} fill="#1E293B" stroke="#475569" strokeWidth={2} />
            {[220, 275, 330, 385, 440, 495, 550, 605, 660, 715, 770, 825].map((rx) => (
              <g key={`roll-${rx}`}>
                <rect x={rx - 8} y={-8} width={16} height={16} rx={3} fill="#475569" stroke="#94A3B8" strokeWidth={1.5} />
                <circle cx={rx} cy={0} r={3} fill="#0F172A" />
              </g>
            ))}
            <rect x={240} y={28} width={24} height={180} fill="#0F172A" stroke="#334155" strokeWidth={2} />
            <rect x={220} y={200} width={64} height={14} rx={3} fill="#1E293B" stroke="#475569" strokeWidth={1.5} />
            <rect x={width - 264} y={28} width={24} height={180} fill="#0F172A" stroke="#334155" strokeWidth={2} />
            <rect x={width - 284} y={200} width={64} height={14} rx={3} fill="#1E293B" stroke="#475569" strokeWidth={1.5} />
            <text x={cx} y={55} textAnchor="middle" fill="#64748B" fontSize={13} fontFamily="monospace" fontWeight={800} letterSpacing="0.2em">
              CONVEYOR FEED LINE // FLOW ►►►
            </text>
          </g>

          <line x1={120} y1={1220} x2={width - 120} y2={1220} stroke="#334155" strokeWidth={2} />
          <line x1={60} y1={1280} x2={width - 60} y2={1280} stroke="#1E293B" strokeWidth={1.5} />

          {/* Warehouse Assembly Station Payload Box */}
          <g transform={`translate(${cx}, ${armY + 70})`}>
            <ellipse cx={0} cy={140} rx={120} ry={22} fill="rgba(0,0,0,0.6)" filter="url(#softGlow1)" />
            <rect x={-70} y={-45} width={140} height={90} rx={10} fill="url(#payloadGrad)" stroke="#60A5FA" strokeWidth={2.5} />
            <line x1={-60} y1={0} x2={60} y2={0} stroke="#93C5FD" strokeWidth={2} strokeDasharray="6 4" />
            <rect x={-45} y={-24} width={90} height={20} rx={4} fill="#0F172A" opacity={0.9} />
            <text x={0} y={-10} textAnchor="middle" fill="#F8FAFC" fontSize={10} fontFamily="monospace" fontWeight={800} letterSpacing="0.06em">
              PAYLOAD 01
            </text>
            <text x={0} y={24} textAnchor="middle" fill="#DBEAFE" fontSize={11} fontFamily="monospace" fontWeight={700}>
              ZERO-SLIP
            </text>
          </g>

          {/* Main Industrial Manipulator Arm */}
          <g transform={`translate(${cx}, ${armY})`}>
            <rect x={-36} y={-420} width={72} height={380} rx={8} fill="url(#armShaftGrad)" stroke="#475569" strokeWidth={2} />
            <line x1={-12} y1={-400} x2={-12} y2={-50} stroke="#64748B" strokeWidth={3} />
            <line x1={12} y1={-400} x2={12} y2={-50} stroke="#64748B" strokeWidth={3} />

            <rect x={-90} y={-45} width={180} height={42} rx={8} fill="#0F172A" stroke="#94A3B8" strokeWidth={2.5} />
            <circle cx={-50} cy={-24} r={6} fill="#475569" />
            <circle cx={50} cy={-24} r={6} fill="#475569" />
            <circle cx={0} cy={-24} r={12} fill="#1E293B" stroke={accent} strokeWidth={2} />

            <g transform={`translate(${-jawGap}, 0)`}>
              <rect x={-140} y={-12} width={65} height={22} rx={3} fill="#334155" stroke="#64748B" strokeWidth={1.5} />
              <path
                d="M -90 -5 L -55 -5 L -42 40 L -42 110 L -68 110 L -68 60 L -90 40 Z"
                fill="url(#jawGradLeft)"
                stroke="#CBD5E1"
                strokeWidth={2}
              />
              <rect x={-45} y={55} width={7} height={50} rx={2} fill={isClamped ? '#22C55E' : accent} filter="url(#softGlow1)" />
            </g>

            <g transform={`translate(${jawGap}, 0)`}>
              <rect x={75} y={-12} width={65} height={22} rx={3} fill="#334155" stroke="#64748B" strokeWidth={1.5} />
              <path
                d="M 90 -5 L 55 -5 L 42 40 L 42 110 L 68 110 L 68 60 L 90 40 Z"
                fill="url(#jawGradRight)"
                stroke="#CBD5E1"
                strokeWidth={2}
              />
              <rect x={38} y={55} width={7} height={50} rx={2} fill={isClamped ? '#22C55E' : accent} filter="url(#softGlow1)" />
            </g>

            {isClamped ? (
              <g>
                <ellipse cx={-42 - jawGap} cy={80} rx={pulseRadius * 0.7} ry={pulseRadius * 0.4} fill="none" stroke="#22C55E" strokeWidth={2} opacity={pulseOpacity} />
                <ellipse cx={42 + jawGap} cy={80} rx={pulseRadius * 0.7} ry={pulseRadius * 0.4} fill="none" stroke="#22C55E" strokeWidth={2} opacity={pulseOpacity} />
              </g>
            ) : null}
          </g>

          {/* DYNAMIC UI CALLOUT PLACEMENT: Angled Leader Line */}
          <polyline
            points={`${hudX - 150},${hudY + 45} ${hudX - 200},${hudY + 120} ${contactX},${contactY}`}
            fill="none"
            stroke="#38BDF8"
            strokeWidth={2}
            strokeDasharray="6 4"
            opacity={0.85}
          />
          <circle cx={contactX} cy={contactY} r={5} fill="#38BDF8" filter="url(#softGlow1)" />

          {/* Floating High-Tech Telemetry HUD Card (Generous 310px width, zero text clipping!) */}
          <g transform={`translate(${hudX}, ${hudY})`}>
            <rect x={-155} y={0} width={310} height={92} rx={12} fill="rgba(15, 23, 42, 0.96)" stroke="#38BDF8" strokeWidth={1.5} />
            <circle cx={-130} cy={24} r={6} fill={isClamped ? '#22C55E' : accent} filter="url(#softGlow1)" />
            <text x={-115} y={28} fill="#F8FAFC" fontSize={13} fontFamily={theme.fontFamily} fontWeight={800} letterSpacing="0.04em">
              {isClamped ? 'TACTILE CLAMP LOCKED' : `ACTUATOR: ${Math.round(clampT * 100)}%`}
            </text>
            <rect x={-130} y={44} width={260} height={8} rx={4} fill="#1E293B" />
            <rect x={-130} y={44} width={260 * (isClamped ? forceProgress : clampT * 0.2)} height={8} rx={4} fill={isClamped ? '#22C55E' : accent} />
            <text x={-130} y={74} fill="#94A3B8" fontSize={11} fontFamily="monospace" fontWeight={700}>
              FORCE: {currentForce} N
            </text>
            <text x={130} y={74} textAnchor="end" fill={isClamped ? '#22C55E' : '#38BDF8'} fontSize={11} fontFamily="monospace" fontWeight={700}>
              1,000 Hz CLOSED-LOOP
            </text>
          </g>
        </svg>
      </AbsoluteFill>
    );
  }

  // ---------------------------------------------------------------------------
  // SCENE 02: MULTI-AXIS ROBOTIC ARM SENSOR FEEDBACK LOOP & DIGITAL TWIN
  // Voiceover: "Live AI control HUD with real-time sensor feedback."
  // Unbalanced framing completely resolved: Heavy industrial 6-axis manipulator
  // with 340px / 290px links, overhead sensor scanning truss, and broad dynamic
  // articulation across the full width and vertical height of the 9:16 frame.
  // ---------------------------------------------------------------------------
  if (sc.includes('scene_02') || sc.includes('sec_02') || sc.includes('kinematic') || sc.includes('cad') || sc.includes('arm')) {
    const cx = width / 2;
    const baseX = 540;
    const baseY = height * 0.68; // y ~ 1300px

    // Fast, energetic articulation cycle
    const cycle = (p * 1.4) % 1;
    const j1Angle = 28.0 + Math.sin(cycle * Math.PI * 2) * 44.0;
    const j2Angle = -24.0 + Math.cos(cycle * Math.PI * 2) * 36.0;
    const len1 = 330; // Substantial reach filling upper space
    const len2 = 280;

    const rad1 = ((j1Angle - 90) * Math.PI) / 180;
    const elbowX = baseX + Math.cos(rad1) * len1;
    const elbowY = baseY + Math.sin(rad1) * len1;

    const rad2 = ((j1Angle + j2Angle - 90) * Math.PI) / 180;
    const wristX = elbowX + Math.cos(rad2) * len2;
    const wristY = elbowY + Math.sin(rad2) * len2;

    const splineT = (p * 3.0) % 1;
    const pulseX = 220 + splineT * 640;
    const pulseY = 660 + Math.sin(splineT * Math.PI) * 110;

    return (
      <AbsoluteFill style={{pointerEvents: 'none'}}>
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id="sensorConeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.04" />
            </linearGradient>
            <linearGradient id="overheadLaserGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.0" />
            </linearGradient>
            <filter id="softGlow2" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 1. OVERHEAD SENSOR & KINEMATIC DIGITAL TWIN TRUSS (Fills upper 420-560px space!) */}
          <g transform="translate(0, 420)">
            <rect x={120} y={0} width={width - 240} height={36} rx={6} fill="#0F172A" stroke="#334155" strokeWidth={2} />
            <line x1={120} y1={18} x2={width - 120} y2={18} stroke="#475569" strokeWidth={1.5} strokeDasharray="8 6" />
            {/* 3 Overhead Laser Depth Sensors */}
            {[260, 540, 820].map((sx, idx) => (
              <g key={`sensor-${idx}`}>
                <circle cx={sx} cy={18} r={10} fill="#1E293B" stroke="#38BDF8" strokeWidth={2} />
                <circle cx={sx} cy={18} r={4} fill={accent} />
                {/* Downward telemetry laser cones */}
                <polygon points={`${sx},28 ${sx - 45},140 ${sx + 45},140`} fill="url(#overheadLaserGrad)" />
                <line x1={sx - 45} y1={140} x2={sx + 45} y2={140} stroke="#F59E0B" strokeWidth={1} strokeDasharray="4 4" opacity={0.6} />
              </g>
            ))}
            <text x={cx} y={-10} textAnchor="middle" fill="#64748B" fontSize={12} fontFamily="monospace" fontWeight={700} letterSpacing="0.1em">
              SPATIAL CALIBRATION ARRAY // 60 FPS OPTICAL TRACKING
            </text>
          </g>

          {/* 2. SIDE STORAGE RACKS & WORKSTATIONS */}
          <g opacity={0.35}>
            <rect x={40} y={480} width={130} height={760} fill="#0F172A" stroke="#334155" strokeWidth={2} />
            {[560, 720, 880, 1040, 1200].map((sy) => (
              <line key={`lshelf-${sy}`} x1={40} y1={sy} x2={170} y2={sy} stroke="#475569" strokeWidth={2} />
            ))}
            <rect x={width - 170} y={480} width={130} height={760} fill="#0F172A" stroke="#334155" strokeWidth={2} />
            {[560, 720, 880, 1040, 1200].map((sy) => (
              <line key={`rshelf-${sy}`} x1={width - 170} y1={sy} x2={width - 40} y2={sy} stroke="#475569" strokeWidth={2} />
            ))}
          </g>

          {/* Staging Workstations */}
          <g transform="translate(240, 1140)">
            <rect x={-80} y={0} width={160} height={140} rx={8} fill="#0F172A" stroke="#475569" strokeWidth={2} />
            <rect x={-65} y={-35} width={130} height={35} rx={6} fill="#1E293B" stroke="#38BDF8" strokeWidth={1.5} />
            <text x={0} y={-12} textAnchor="middle" fill="#38BDF8" fontSize={12} fontFamily="monospace" fontWeight={800}>
              PICK STATION A
            </text>
          </g>
          <g transform="translate(840, 1140)">
            <rect x={-80} y={0} width={160} height={140} rx={8} fill="#0F172A" stroke="#475569" strokeWidth={2} />
            <rect x={-65} y={-35} width={130} height={35} rx={6} fill="#1E293B" stroke={accent} strokeWidth={1.5} />
            <text x={0} y={-12} textAnchor="middle" fill={accent} fontSize={12} fontFamily="monospace" fontWeight={800}>
              INSPECT STATION B
            </text>
          </g>

          {/* Baseline Floor */}
          <line x1={40} y1={baseY + 100} x2={width - 40} y2={baseY + 100} stroke="#334155" strokeWidth={2.5} />
          <line x1={20} y1={baseY + 160} x2={width - 20} y2={baseY + 160} stroke="#1E293B" strokeWidth={2} />

          {/* Broad, High-Arching Motion Trajectory Spline */}
          <path
            d="M 220 880 C 360 520, 720 520, 860 880"
            fill="none"
            stroke="#38BDF8"
            strokeWidth={3.5}
            strokeDasharray="10 8"
            opacity={0.85}
            filter="url(#softGlow2)"
          />
          <circle cx={pulseX} cy={pulseY} r={10} fill={accent} filter="url(#softGlow2)" />
          <circle cx={pulseX} cy={pulseY} r={4} fill="#FFFFFF" />

          {/* Laser Depth Scanner Cone */}
          <polygon
            points={`${wristX},${wristY} ${wristX - 120},${wristY + 230} ${wristX + 120},${wristY + 230}`}
            fill="url(#sensorConeGrad)"
          />
          <line x1={wristX - 120} y1={wristY + 230} x2={wristX + 120} y2={wristY + 230} stroke="#38BDF8" strokeWidth={2} opacity={0.7} />

          {/* Heavy Robotic Arm Base Platform */}
          <g transform={`translate(${baseX}, ${baseY})`}>
            <rect x={-120} y={0} width={240} height={46} rx={8} fill="#0F172A" stroke="#64748B" strokeWidth={2.5} />
            <circle cx={0} cy={0} r={48} fill="#1E293B" stroke="#38BDF8" strokeWidth={3} />
            <circle cx={0} cy={0} r={20} fill="#0F172A" stroke={accent} strokeWidth={2.5} />
          </g>

          {/* Massive Upper Arm Link */}
          <line x1={baseX} y1={baseY} x2={elbowX} y2={elbowY} stroke="#94A3B8" strokeWidth={30} strokeLinecap="round" />
          <line x1={baseX} y1={baseY} x2={elbowX} y2={elbowY} stroke="#0F172A" strokeWidth={14} strokeLinecap="round" />

          {/* Elbow Joint Housing */}
          <circle cx={elbowX} cy={elbowY} r={34} fill="#1E293B" stroke="#38BDF8" strokeWidth={3.5} />
          <circle cx={elbowX} cy={elbowY} r={14} fill={accent} />

          {/* Massive Forearm Link */}
          <line x1={elbowX} y1={elbowY} x2={wristX} y2={wristY} stroke="#64748B" strokeWidth={22} strokeLinecap="round" />
          <line x1={elbowX} y1={elbowY} x2={wristX} y2={wristY} stroke="#0F172A" strokeWidth={10} strokeLinecap="round" />

          {/* Wrist Tool & End-Effector */}
          <circle cx={wristX} cy={wristY} r={20} fill="#38BDF8" />
          <line x1={wristX - 34} y1={wristY} x2={wristX + 34} y2={wristY} stroke={accent} strokeWidth={8} strokeLinecap="round" />

          {/* Telemetry Dials */}
          <g transform={`translate(${baseX + 130}, ${baseY - 60})`}>
            <rect x={0} y={-18} width={180} height={36} rx={8} fill="rgba(15, 23, 42, 0.94)" stroke="#38BDF8" strokeWidth={1.5} />
            <text x={12} y={5} fill="#38BDF8" fontSize={13} fontFamily="monospace" fontWeight={800}>
              J1: +{j1Angle.toFixed(1)}° [TRACKING]
            </text>
          </g>
          <g transform={`translate(${elbowX + 50}, ${elbowY - 25})`}>
            <rect x={0} y={-16} width={160} height={32} rx={6} fill="rgba(15, 23, 42, 0.94)" stroke="#64748B" strokeWidth={1} />
            <text x={10} y={5} fill="#F8FAFC" fontSize={12} fontFamily="monospace" fontWeight={700}>
              J2: {j2Angle.toFixed(1)}°
            </text>
          </g>

          {/* Top HUD Banner */}
          <g transform={`translate(${width / 2}, 360)`}>
            <rect x={-230} y={-22} width={460} height={44} rx={10} fill="rgba(15, 23, 42, 0.96)" stroke="#334155" strokeWidth={1.5} />
            <circle cx={-205} cy={0} r={5} fill="#22C55E" />
            <text x={-190} y={5} fill="#F8FAFC" fontSize={13} fontFamily={theme.fontFamily} fontWeight={800} letterSpacing="0.04em">
              GPT-6 ASTRA KINEMATIC LOOP
            </text>
            <text x={205} y={5} textAnchor="end" fill="#38BDF8" fontSize={12} fontFamily="monospace" fontWeight={700}>
              LATENCY: 1.2ms
            </text>
          </g>
        </svg>
      </AbsoluteFill>
    );
  }


  // ---------------------------------------------------------------------------
  // SCENE 03: AUTONOMOUS MOBILE ROBOT (AMR) DYNAMIC OBSTACLE RE-ROUTING
  // Voiceover: "Autonomous logistics machines dynamically rerouting around obstacles."
  // Warehouse Aisle Architecture: Concrete storage bays (BAY A-01..04, BAY B-01..04),
  // industrial yellow/black floor hazard boundary lines, dropped pallet obstacle.
  // 1.35x faster AMR velocity and fluid banking bypass curve.
  // ---------------------------------------------------------------------------
  if (sc.includes('scene_03') || sc.includes('sec_03') || sc.includes('path') || sc.includes('rover') || sc.includes('obstacle')) {
    let rx = 540;
    let ry = 1380;
    let heading = 0;
    let statusText = 'NOMINAL AISLE CORRIDOR';
    let statusColor = '#38BDF8';
    let isDetecting = false;

    // 1.35x Snappier Navigation Motion
    if (p < 0.25) {
      const sub = p / 0.25;
      rx = 540;
      ry = 1380 - sub * 280;
      heading = 0;
      statusText = 'APPROACHING // BAY A-03';
      statusColor = '#38BDF8';
    } else if (p < 0.70) {
      const sub = (p - 0.25) / 0.45;
      const angleRad = sub * Math.PI;
      rx = 540 + Math.sin(angleRad) * 170; // swings into right clearance lane
      ry = 1100 - sub * 360;
      heading = Math.cos(angleRad) * 32; // dynamic banking angle
      isDetecting = true;
      statusText = 'OBSTACLE DETECTED // DYNAMIC REROUTE';
      statusColor = accent;
    } else {
      const sub = (p - 0.70) / 0.30;
      rx = 540;
      ry = 740 - sub * 240;
      heading = 0;
      statusText = 'BYPASS CONFIRMED // NOMINAL FLOW';
      statusColor = '#22C55E';
    }

    const lidarSweep = Math.sin(p * Math.PI * 14) * 34;

    return (
      <AbsoluteFill style={{pointerEvents: 'none'}}>
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id="lidarConeGrad3" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor={isDetecting ? accent : '#38BDF8'} stopOpacity="0.5" />
              <stop offset="100%" stopColor={isDetecting ? accent : '#38BDF8'} stopOpacity="0.04" />
            </linearGradient>
            <filter id="softGlow3" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* 1. ENVIRONMENTAL WAREHOUSE ARCHITECTURE: High-Bay Storage Rack Bays (Both Sides) */}
          {/* Left Bay Structure (Bay A-01 to A-04) */}
          <g>
            <rect x={20} y={440} width={220} height={1020} fill="#0F172A" stroke="#334155" strokeWidth={2.5} />
            {[480, 720, 960, 1200].map((by, idx) => (
              <g key={`bayA-${idx}`}>
                <line x1={20} y1={by} x2={240} y2={by} stroke="#475569" strokeWidth={2} />
                <rect x={35} y={by + 15} width={190} height={200} rx={4} fill="#1E293B" stroke="#334155" strokeWidth={1} />
                {/* Pallet crate contents inside bay */}
                <rect x={55} y={by + 40} width={150} height={150} rx={6} fill="#0F172A" stroke="#64748B" strokeWidth={1.5} />
                <text x={130} y={by + 120} textAnchor="middle" fill="#94A3B8" fontSize={13} fontFamily="monospace" fontWeight={800}>
                  {`BAY A-0${idx + 1}`}
                </text>
              </g>
            ))}
          </g>
          {/* Right Bay Structure (Bay B-01 to B-04) */}
          <g>
            <rect x={width - 240} y={440} width={220} height={1020} fill="#0F172A" stroke="#334155" strokeWidth={2.5} />
            {[480, 720, 960, 1200].map((by, idx) => (
              <g key={`bayB-${idx}`}>
                <line x1={width - 240} y1={by} x2={width - 20} y2={by} stroke="#475569" strokeWidth={2} />
                <rect x={width - 225} y={by + 15} width={190} height={200} rx={4} fill="#1E293B" stroke="#334155" strokeWidth={1} />
                {/* Pallet crate contents inside bay */}
                <rect x={width - 205} y={by + 40} width={150} height={150} rx={6} fill="#0F172A" stroke="#64748B" strokeWidth={1.5} />
                <text x={width - 130} y={by + 120} textAnchor="middle" fill="#94A3B8" fontSize={13} fontFamily="monospace" fontWeight={800}>
                  {`BAY B-0${idx + 1}`}
                </text>
              </g>
            ))}
          </g>

          {/* 2. INDUSTRIAL FLOOR AISLE MARKINGS & HAZARD STRIPES */}
          {/* Yellow/Black Chevron Hazard Lane Borders */}
          <line x1={260} y1={440} x2={260} y2={1460} stroke="#F59E0B" strokeWidth={3} strokeDasharray="14 10" />
          <line x1={width - 260} y1={440} x2={width - 260} y2={1460} stroke="#F59E0B" strokeWidth={3} strokeDasharray="14 10" />
          {/* Central Lane Guidance Track */}
          <line x1={540} y1={440} x2={540} y2={1460} stroke="#334155" strokeWidth={2} strokeDasharray="10 10" />

          {/* Dynamic Computed Bypass Spline Curve */}
          <path
            d="M 540 1380 L 540 1100 C 540 980 710 980 710 920 C 710 860 540 860 540 500"
            fill="none"
            stroke={isDetecting ? accent : '#22C55E'}
            strokeWidth={4}
            strokeDasharray="12 6"
            opacity={0.9}
          />

          {/* 3. PHYSICAL OBSTACLE: DROPPED WOODEN PALLET WITH SPILLED INDUSTRIAL CRATE */}
          <g transform="translate(540, 920)">
            {/* Safety Proximity Zone Perimeter */}
            <circle cx={0} cy={0} r={115} fill="none" stroke="#EF4444" strokeWidth={2} strokeDasharray="8 6" opacity={isDetecting ? 0.85 : 0.4} />
            {/* Wooden Pallet Base Runners */}
            <rect x={-90} y={-50} width={180} height={100} rx={8} fill="#271E18" stroke="#D97706" strokeWidth={2} />
            <line x1={-90} y1={-16} x2={90} y2={-16} stroke="#78350F" strokeWidth={3} />
            <line x1={-90} y1={18} x2={90} y2={18} stroke="#78350F" strokeWidth={3} />
            {/* Dropped Spilled Cargo Box */}
            <rect x={-55} y={-35} width={110} height={70} rx={6} fill="#18181B" stroke="#EF4444" strokeWidth={2.5} />
            {/* Hazard Stripe Decal */}
            <line x1={-40} y1={-20} x2={-15} y2={20} stroke="#EF4444" strokeWidth={3} />
            <line x1={-10} y1={-20} x2={15} y2={20} stroke="#EF4444" strokeWidth={3} />
            <line x1={20} y1={-20} x2={45} y2={20} stroke="#EF4444" strokeWidth={3} />
            {/* High-Visibility Mobile Hazard Badge */}
            <rect x={-80} y={-14} width={160} height={28} rx={6} fill="#7F1D1D" />
            <text x={0} y={5} textAnchor="middle" fill="#FFFFFF" fontSize={13} fontFamily="monospace" fontWeight={900} letterSpacing="0.04em">
              OBSTACLE // 1.8m
            </text>
          </g>

          {/* Autonomous Mobile Robot (AMR) Actor */}
          <g transform={`translate(${rx}, ${ry}) rotate(${heading})`}>
            {/* Sweeping LiDAR Fan (120°) */}
            <g transform={`rotate(${lidarSweep})`}>
              <path
                d="M 0 0 L -110 -200 A 230 230 0 0 1 110 -200 Z"
                fill="url(#lidarConeGrad3)"
                stroke={isDetecting ? accent : '#38BDF8'}
                strokeWidth={1.5}
                opacity={0.85}
              />
              <line x1={0} y1={0} x2={0} y2={-205} stroke={isDetecting ? accent : '#38BDF8'} strokeWidth={2.5} opacity={0.9} />
            </g>

            {/* AMR Heavy-Duty Chassis */}
            <rect x={-46} y={-58} width={92} height={116} rx={16} fill="#0F172A" stroke="#F1F5F9" strokeWidth={3} />
            {/* Drive wheels */}
            <rect x={-54} y={-48} width={10} height={96} rx={4} fill="#334155" stroke="#64748B" strokeWidth={1} />
            <rect x={44} y={-48} width={10} height={96} rx={4} fill="#334155" stroke="#64748B" strokeWidth={1} />
            {/* Top rotating LiDAR scanner */}
            <circle cx={0} cy={-16} r={20} fill="#1E293B" stroke={accent} strokeWidth={2.5} />
            <circle cx={0} cy={-16} r={7} fill={statusColor} />
            {/* Direction chevron */}
            <polygon points="-12,24 12,24 0,8" fill="#94A3B8" />

            {/* Locked High-Contrast Telemetry Tag */}
            <g transform="translate(64, -14)">
              <rect x={0} y={-15} width={145} height={30} rx={6} fill="rgba(15, 23, 42, 0.95)" stroke="#475569" strokeWidth={1.5} />
              <text x={10} y={5} fill={statusColor} fontSize={13} fontFamily="monospace" fontWeight={800}>
                AMR // 2.2 m/s
              </text>
            </g>
          </g>

          {/* Top Global Navigation HUD Card */}
          <g transform={`translate(${width / 2}, 360)`}>
            <rect x={-210} y={-22} width={420} height={44} rx={10} fill="rgba(15, 23, 42, 0.96)" stroke={statusColor} strokeWidth={1.5} />
            <circle cx={-185} cy={0} r={5} fill={statusColor} />
            <text x={-168} y={5} fill="#F8FAFC" fontSize={13} fontFamily="monospace" fontWeight={800}>
              {statusText}
            </text>
          </g>
        </svg>
      </AbsoluteFill>
    );
  }

  // ---------------------------------------------------------------------------
  // SCENE 04: COORDINATED WAREHOUSE AMR FLEET 3D PERSPECTIVE TRAVERSAL
  // Voiceover: "High-throughput dual-channel automated logistics flow."
  // True 3D Perspective Projection: Vanishing point at (540, 380).
  // Perspective aisle lines, high-bay trusses, and AMRs travel directly from deep
  // background aisle toward foreground camera (scaling 0.35x -> 1.35x).
  // Large, bold mobile telemetry badges (18-20px font, easily legible on phone!).
  // ---------------------------------------------------------------------------
  if (sc.includes('scene_04') || sc.includes('sec_04') || sc.includes('fleet') || sc.includes('warehouse') || sc.includes('logistic')) {
    const vpX = 540;
    const vpY = 380; // Vanishing Point at deep horizon

    // 3D Perspective Traversal Formula:
    // depth parameter d in [0, 1]
    // y(d) = vpY + d^1.6 * (height - vpY)
    // scale(d) = 0.35 + d * 0.95
    // x(d) = vpX + laneOffset * (0.15 + d * 0.85)

    // Unit 1 (Hero Foreground Left Lane): Approaches closest to camera
    const d1 = Math.min(1, Math.max(0, (p * 1.35 + 0.15) % 1.25));
    const u1_scale = 0.35 + d1 * 0.95;
    const u1_y = vpY + Math.pow(d1, 1.4) * 980;
    const u1_x = vpX - 260 * (0.2 + d1 * 0.8);

    // Unit 2 (Midground Right Lane): Following staggered rhythm
    const d2 = Math.min(1, Math.max(0, (p * 1.35 + 0.6) % 1.25));
    const u2_scale = 0.35 + d2 * 0.85;
    const u2_y = vpY + Math.pow(d2, 1.4) * 920;
    const u2_x = vpX + 260 * (0.2 + d2 * 0.8);

    // Unit 3 (Distant Center Swarm Unit): Trailing at horizon
    const d3 = Math.min(1, Math.max(0, (p * 1.35) % 1.25));
    const u3_scale = 0.35 + d3 * 0.65;
    const u3_y = vpY + Math.pow(d3, 1.4) * 780;
    const u3_x = vpX + 30 * (0.1 + d3 * 0.9);

    return (
      <AbsoluteFill style={{pointerEvents: 'none'}}>
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id="perspFloorGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0B132B" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#0F172A" stopOpacity="0.95" />
            </linearGradient>
            <linearGradient id="headlightBeam" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.0" />
            </linearGradient>
            <filter id="shadowBlur4" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" />
            </filter>
          </defs>

          {/* 1. TRUE 3D PERSPECTIVE WAREHOUSE FLOOR LINES (Radiating from Vanishing Point) */}
          <line x1={vpX} y1={vpY} x2={40} y2={height} stroke="#334155" strokeWidth={2.5} />
          <line x1={vpX} y1={vpY} x2={260} y2={height} stroke="#F59E0B" strokeWidth={3} strokeDasharray="14 10" />
          <line x1={vpX} y1={vpY} x2={540} y2={height} stroke="#334155" strokeWidth={2} strokeDasharray="8 8" />
          <line x1={vpX} y1={vpY} x2={820} y2={height} stroke="#F59E0B" strokeWidth={3} strokeDasharray="14 10" />
          <line x1={vpX} y1={vpY} x2={width - 40} y2={height} stroke="#334155" strokeWidth={2.5} />

          {/* Perspective Warehouse High-Bay Truss Silhouettes */}
          <line x1={vpX} y1={vpY - 60} x2={60} y2={180} stroke="#1E293B" strokeWidth={2} />
          <line x1={vpX} y1={vpY - 60} x2={width - 60} y2={180} stroke="#1E293B" strokeWidth={2} />

          {/* Perspective Distance Grid Crossbars (Stepping into Depth) */}
          {[0.2, 0.4, 0.6, 0.8, 1.0].map((step, idx) => {
            const gy = vpY + Math.pow(step, 1.5) * (height - vpY - 80);
            const span = 180 + step * 760;
            return (
              <line
                key={`pgrid-${idx}`}
                x1={vpX - span / 2}
                y1={gy}
                x2={vpX + span / 2}
                y2={gy}
                stroke="#1E293B"
                strokeWidth={1.5}
                opacity={0.4 + step * 0.4}
              />
            );
          })}

          {/* Unit 03 (Distant fleet member) */}
          <g transform={`translate(${u3_x}, ${u3_y}) scale(${u3_scale})`}>
            <ellipse cx={0} cy={35} rx={60} ry={16} fill="rgba(0,0,0,0.6)" filter="url(#shadowBlur4)" />
            <polygon points="-25,0 -50,-120 50,-120 25,0" fill="url(#headlightBeam)" />
            <rect x={-40} y={-30} width={80} height={60} rx={8} fill="#1E293B" stroke="#64748B" strokeWidth={2} />
            <rect x={-26} y={-18} width={52} height={36} rx={3} fill="#2563EB" opacity={0.85} />
          </g>

          {/* Unit 02 (Midground right lane) */}
          <g transform={`translate(${u2_x}, ${u2_y}) scale(${u2_scale})`}>
            <ellipse cx={0} cy={55} rx={95} ry={24} fill="rgba(0,0,0,0.65)" filter="url(#shadowBlur4)" />
            <polygon points="-40,0 -90,-180 90,-180 40,0" fill="url(#headlightBeam)" />
            <ellipse cx={0} cy={0} rx={95} ry={70} fill="none" stroke="#38BDF8" strokeWidth={2} strokeDasharray="6 4" opacity={0.6} />
            {/* Chassis */}
            <rect x={-65} y={-50} width={130} height={100} rx={14} fill="#0F172A" stroke="#94A3B8" strokeWidth={2.5} />
            <rect x={-50} y={-35} width={100} height={70} rx={8} fill="#1D4ED8" stroke="#60A5FA" strokeWidth={2} />
            {/* Large Bold Mobile Tag */}
            <g transform="translate(0, 75)">
              <rect x={-80} y={-15} width={160} height={30} rx={6} fill="#0F172A" stroke="#38BDF8" strokeWidth={1.5} />
              <text x={0} y={6} textAnchor="middle" fill="#38BDF8" fontSize={16} fontFamily="monospace" fontWeight={900}>
                AMR 02 // 3.8 m/s
              </text>
            </g>
          </g>

          {/* Unit 01 (Hero Foreground Left Lane) */}
          <g transform={`translate(${u1_x}, ${u1_y}) scale(${u1_scale})`}>
            <ellipse cx={0} cy={75} rx={135} ry={30} fill="rgba(0,0,0,0.75)" filter="url(#shadowBlur4)" />
            <polygon points="-60,0 -130,-240 130,-240 60,0" fill="url(#headlightBeam)" opacity={0.6} />
            <ellipse cx={0} cy={0} rx={135} ry={95} fill="none" stroke={accent} strokeWidth={2.5} strokeDasharray="8 6" opacity={0.75} />
            {/* Main Chassis Body */}
            <rect x={-90} y={-70} width={180} height={140} rx={18} fill="#0F172A" stroke="#F8FAFC" strokeWidth={3} />
            <rect x={-75} y={-50} width={150} height={100} rx={10} fill="#2563EB" stroke="#93C5FD" strokeWidth={2.5} />
            <text x={0} y={8} textAnchor="middle" fill="#FFFFFF" fontSize={19} fontFamily="monospace" fontWeight={900}>
              HERO AMR 01
            </text>
            <rect x={-80} y={-64} width={160} height={8} rx={4} fill="#38BDF8" />
            {/* Large Bold Mobile Telemetry Badge (18px+) */}
            <g transform="translate(0, 96)">
              <rect x={-120} y={-18} width={240} height={36} rx={8} fill="rgba(15, 23, 42, 0.98)" stroke={accent} strokeWidth={2} />
              <text x={0} y={6} textAnchor="middle" fill={accent} fontSize={18} fontFamily="monospace" fontWeight={900} letterSpacing="0.04em">
                VELOCITY: 4.2 m/s
              </text>
            </g>
          </g>

          {/* Facility Swarm Performance HUD */}
          <g transform={`translate(${width / 2}, 360)`}>
            <rect x={-230} y={-22} width={460} height={44} rx={10} fill="rgba(15, 23, 42, 0.96)" stroke="#334155" strokeWidth={1.5} />
            <circle cx={-205} cy={0} r={5} fill="#22C55E" />
            <text x={-190} y={5} fill="#F8FAFC" fontSize={13} fontFamily="monospace" fontWeight={800}>
              FLEET SWARM: 12 UNITS // SYNC 99.8%
            </text>
            <text x={205} y={5} textAnchor="end" fill="#22C55E" fontSize={12} fontFamily="monospace" fontWeight={800}>
              DELAY: 0.0s
            </text>
          </g>
        </svg>
      </AbsoluteFill>
    );
  }
}

  // ---------------------------------------------------------------------------
  // SCENE 05: OUTRO & ANIMATED YOUTUBE SUBSCRIBE INTERACTION
  // Minimalist, high-production design: Clean channel logo + dynamic YouTube
  // subscribe button with cursor click, state transition to SUBSCRIBED, and
  // ringing notification bell animation. Zero taglines per user direction.
  // ---------------------------------------------------------------------------
  if (sc.includes('scene_05') || sc.includes('sec_05') || sc.includes('global') || sc.includes('neural') || sc.includes('core') || sc.includes('brand') || sc.includes('cta')) {
    const cx = width / 2;
    const logoY = 720;
    const subscribeY = 1040;

    const floatY = Math.sin(p * Math.PI * 3) * 6;
    const isClicked = p >= 0.40;
    const isBellRung = p >= 0.72;

    // Button scale on click moment (0.38 - 0.46)
    const btnScale = p >= 0.38 && p < 0.46 ? 0.94 : 1.0;

    // Cursor swoop interpolation
    let cursorX = cx + 220;
    let cursorY = 1260;
    let cursorOpacity = 0;

    if (p >= 0.15 && p < 0.55) {
      // Moving to SUBSCRIBE button
      const t = Math.min(1, Math.max(0, (p - 0.15) / 0.23));
      cursorOpacity = Math.min(1, (p - 0.15) / 0.08);
      cursorX = cx + 220 - t * 180;
      cursorY = 1260 - t * 220;
    } else if (p >= 0.55 && p < 0.85) {
      // Moving to Bell icon
      const t = Math.min(1, Math.max(0, (p - 0.55) / 0.15));
      cursorOpacity = 1;
      cursorX = cx + 40 + t * 130;
      cursorY = 1040 + t * 5;
    } else if (p >= 0.85) {
      cursorOpacity = Math.max(0, 1 - (p - 0.85) / 0.12);
      cursorX = cx + 170;
      cursorY = 1045 + (p - 0.85) * 120;
    }

    // Bell harmonic vibration on ring
    const bellRot = isBellRung
      ? Math.sin((p - 0.72) * Math.PI * 16) * 18 * Math.max(0, 1 - (p - 0.72) * 3.5)
      : 0;

    // Click wave ripple expansion
    const clickRipple = p >= 0.40 && p < 0.60 ? (p - 0.40) / 0.20 : 0;
    const bellRipple = p >= 0.72 && p < 0.92 ? (p - 0.72) / 0.20 : 0;

    return (
      <AbsoluteFill style={{pointerEvents: 'none'}}>
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <defs>
            <linearGradient id="ytRedGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#EF4444" />
              <stop offset="100%" stopColor="#DC2626" />
            </linearGradient>
            <linearGradient id="logoBorderGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#2563EB" />
              <stop offset="50%" stopColor="#D97706" />
              <stop offset="100%" stopColor="#2563EB" />
            </linearGradient>
            <filter id="claudeOutroCardShadow" x="-15%" y="-15%" width="130%" height="130%">
              <feDropShadow dx="0" dy="8" stdDeviation="16" floodColor="#000000" floodOpacity="0.07" />
            </filter>
            <filter id="ytGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            <filter id="cursorShadow" x="-30%" y="-30%" width="160%" height="160%">
              <feDropShadow dx="2" dy="4" stdDeviation="4" floodColor="#000000" floodOpacity="0.4" />
            </filter>
          </defs>

          {/* Ambient Warm Atmosphere Glow behind card */}
          <circle cx={cx} cy={logoY + 40} r={280} fill="#D97706" opacity={0.04} filter="url(#ytGlow)" />
          <circle cx={cx} cy={logoY + 40} r={180} fill="#2563EB" opacity={0.03} filter="url(#ytGlow)" />

          {/* Central Pure White Card Container (#FFFFFF, #E5E7EB border, soft drop shadow) */}
          <rect
            x={cx - 360}
            y={logoY - 150}
            width={720}
            height={580}
            rx={28}
            fill="#FFFFFF"
            stroke="#E5E7EB"
            strokeWidth={2}
            filter="url(#claudeOutroCardShadow)"
          />

          {/* Clean Channel Logo (Zero Taglines) */}
          <g transform={`translate(${cx}, ${logoY + floatY - 20})`}>
            {/* Hexagonal Outer Emblem */}
            <polygon
              points="0,-85 74,-42 74,42 0,85 -74,42 -74,-42"
              fill="#FFFFFF"
              stroke="url(#logoBorderGrad)"
              strokeWidth={3.5}
            />
            {/* Inner Plate */}
            <polygon
              points="0,-68 58,-34 58,34 0,68 -58,34 -58,-34"
              fill="#F8FAFC"
              stroke="#E2E8F0"
              strokeWidth={1.5}
            />
            {/* Monogram in Charcoal Black */}
            <text x={0} y={16} textAnchor="middle" fill="#1A1917" fontSize={42} fontFamily="sans-serif" fontWeight={900} letterSpacing="0.06em">
              AI
            </text>

            {/* Brand Title (Clean, Bold Charcoal, Zero Taglines) */}
            <text x={0} y={135} textAnchor="middle" fill="#1A1917" fontSize={36} fontFamily="sans-serif" fontWeight={900} letterSpacing="0.05em">
              AI SIMPLIFIED LAB
            </text>
          </g>

          {/* Animated YouTube Subscribe Interaction Container */}
          <g transform={`translate(${cx}, ${subscribeY - 10}) scale(${btnScale})`}>
            {/* Click Ripple Effect */}
            {clickRipple > 0 ? (
              <rect
                x={-200 - clickRipple * 40}
                y={-40 - clickRipple * 20}
                width={400 + clickRipple * 80}
                height={80 + clickRipple * 40}
                rx={40 + clickRipple * 20}
                fill="none"
                stroke="#D97706"
                strokeWidth={3}
                opacity={Math.max(0, 0.8 * (1 - clickRipple))}
              />
            ) : null}

            {/* Main Subscribe Button Pill */}
            <g transform={isClicked ? 'translate(-50, 0)' : 'translate(0, 0)'}>
              <rect
                x={isClicked ? -155 : -190}
                y={-38}
                width={isClicked ? 310 : 380}
                height={76}
                rx={38}
                fill={isClicked ? '#F1F5F9' : 'url(#ytRedGrad)'}
                stroke={isClicked ? '#CBD5E1' : 'none'}
                strokeWidth={isClicked ? 1.5 : 0}
                filter={!isClicked ? 'url(#ytGlow)' : undefined}
              />

              {!isClicked ? (
                // State A: SUBSCRIBE (Red YouTube style)
                <g>
                  {/* YouTube Play Icon */}
                  <polygon points="-125,-12 -100,0 -125,12" fill="#FFFFFF" />
                  <text x={18} y={10} textAnchor="middle" fill="#FFFFFF" fontSize={26} fontFamily="sans-serif" fontWeight={900} letterSpacing="0.06em">
                    SUBSCRIBE
                  </text>
                </g>
              ) : (
                // State B: SUBSCRIBED (Neutral Slate with checkmark)
                <g>
                  {/* Checkmark Icon */}
                  <path d="M -125 0 L -115 10 L -102 -6" fill="none" stroke="#2563EB" strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" />
                  <text x={20} y={9} textAnchor="middle" fill="#1A1917" fontSize={22} fontFamily="sans-serif" fontWeight={800} letterSpacing="0.04em">
                    SUBSCRIBED
                  </text>
                </g>
              )}
            </g>

            {/* Notification Bell Icon (Appears when subscribed) */}
            {isClicked ? (
              <g transform={`translate(160, 0) rotate(${bellRot})`}>
                {/* Bell Circle Housing */}
                <circle cx={0} cy={0} r={36} fill="#FFFFFF" stroke="#CBD5E1" strokeWidth={1.5} filter="url(#claudeOutroCardShadow)" />

                {/* Bell Ripple Waves */}
                {bellRipple > 0 ? (
                  <circle cx={0} cy={0} r={36 + bellRipple * 35} fill="none" stroke="#D97706" strokeWidth={2.5} opacity={Math.max(0, 0.8 * (1 - bellRipple))} />
                ) : null}

                {/* Bell Vector Graphic */}
                <path
                  d="M -11 6 C -11 -6 -6 -13 0 -14 C 6 -13 11 -6 11 6 L 14 10 L -14 10 Z"
                  fill={isBellRung ? '#D97706' : '#64748B'}
                />
                <circle cx={0} cy={14} r={3} fill={isBellRung ? '#D97706' : '#64748B'} />
                <circle cx={0} cy={-16} r={2} fill={isBellRung ? '#D97706' : '#64748B'} />

                {/* Acoustic Sound Ring Waves when Bell Rings */}
                {isBellRung ? (
                  <g stroke="#D97706" strokeWidth={2.5} strokeLinecap="round" fill="none">
                    <path d="M 18 -8 Q 23 0 18 8" />
                    <path d="M -18 -8 Q -23 0 -18 8" />
                  </g>
                ) : null}
              </g>
            ) : null}
          </g>

          {/* Animated Mouse Cursor Pointer with Realistic Hover & Click */}
          {cursorOpacity > 0 ? (
            <g
              transform={`translate(${cursorX}, ${cursorY - 10}) scale(1.4)`}
              opacity={cursorOpacity}
              filter="url(#cursorShadow)"
            >
              {/* Sleek SVG Cursor Arrow */}
              <path
                d="M 0 0 L 0 22 L 6 16 L 13 23 L 17 19 L 10 12 L 17 12 Z"
                fill="#FFFFFF"
                stroke="#18181B"
                strokeWidth={1.75}
                strokeLinejoin="round"
              />
            </g>
          ) : null}
        </svg>
      </AbsoluteFill>
    );
  }

  return null;
};
