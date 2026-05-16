"use client";

export const dynamic = "force-dynamic";

import Link from "next/link";
import {
  Shield,
  Zap,
  MessageSquare,
  Users,
  BarChart3,
  FileText,
  Activity,
  Radio,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Lock,
  Globe,
  Briefcase,
  HeartHandshake,
  Factory,
  Gavel,
  DollarSign,
  Megaphone,
  ChevronDown,
} from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

const features = [
  {
    icon: <Shield className="w-6 h-6 text-red-500" />,
    title: "Crisis Detection & Declaration",
    desc: "Instantly declare crises with severity scoring, category tagging, and automated escalation paths.",
  },
  {
    icon: <Users className="w-6 h-6 text-blue-500" />,
    title: "Response Team Command",
    desc: "Assign Incident Commanders, Legal Counsel, and Comms Leads with clear role-based ownership.",
  },
  {
    icon: <CheckCircle2 className="w-6 h-6 text-green-500" />,
    title: "Action Item Tracker",
    desc: "Kanban-style boards for tracking response tasks from pending to completed with priority flags.",
  },
  {
    icon: <MessageSquare className="w-6 h-6 text-purple-500" />,
    title: "Stakeholder Communications",
    desc: "Centralized comms log for internal updates, executive briefs, stakeholder alerts, and public statements.",
  },
  {
    icon: <FileText className="w-6 h-6 text-amber-500" />,
    title: "Playbook Engine",
    desc: "Pre-built and customizable response playbooks that auto-spawn action items for any crisis type.",
  },
  {
    icon: <BarChart3 className="w-6 h-6 text-indigo-500" />,
    title: "Real-Time Dashboard",
    desc: "Live metrics on active crises, resolution times, severity breakdowns, and team performance.",
  },
  {
    icon: <Zap className="w-6 h-6 text-orange-500" />,
    title: "AI Copilot (Coming Soon)",
    desc: "Auto-generate executive summaries, draft communications, and get next-best-action recommendations.",
  },
  {
    icon: <Activity className="w-6 h-6 text-teal-500" />,
    title: "Audit & Timeline",
    desc: "Immutable chronological logs of every decision, status change, and communication for compliance.",
  },
];

const steps = [
  {
    icon: <AlertTriangle className="w-8 h-8 text-red-500" />,
    title: "1. Detect & Declare",
    desc: "A crisis is detected. Your team declares it in seconds with severity, category, and impact estimates.",
  },
  {
    icon: <Users className="w-8 h-8 text-blue-500" />,
    title: "2. Assemble & Assign",
    desc: "The response team is notified. Roles are assigned and action items are auto-created from playbooks.",
  },
  {
    icon: <Radio className="w-8 h-8 text-purple-500" />,
    title: "3. Coordinate & Communicate",
    desc: "All updates, decisions, and stakeholder comms live in one place — no more lost Slack threads.",
  },
  {
    icon: <TrendingUp className="w-8 h-8 text-green-500" />,
    title: "4. Resolve & Learn",
    desc: "Track resolution metrics, run post-mortems, and refine playbooks for the next incident.",
  },
];

const crisisTypes = [
  { icon: <Factory className="w-5 h-5" />, label: "Operational" },
  { icon: <Lock className="w-5 h-5" />, label: "Security" },
  { icon: <Gavel className="w-5 h-5" />, label: "Legal" },
  { icon: <Megaphone className="w-5 h-5" />, label: "PR" },
  { icon: <Globe className="w-5 h-5" />, label: "Supply Chain" },
  { icon: <HeartHandshake className="w-5 h-5" />, label: "HR" },
  { icon: <DollarSign className="w-5 h-5" />, label: "Financial" },
  { icon: <Briefcase className="w-5 h-5" />, label: "Other" },
];

const testimonials = [
  {
    quote: "During our product recall, DClaw Crisis cut our response coordination time by 60%. Every stakeholder knew exactly what to do.",
    name: "Sarah Chen",
    role: "VP of Operations, Fortune 500 Retailer",
  },
  {
    quote: "We went from scattered email chains to a single command center. Our legal and PR teams finally speak the same language.",
    name: "Marcus Johnson",
    role: "General Counsel, SaaS Unicorn",
  },
  {
    quote: "The playbook engine alone saved us hours during a cyber incident. Auto-spawned action items meant nothing fell through the cracks.",
    name: "Priya Nair",
    role: "CISO, Fintech Scale-up",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* NAVBAR */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-red-600" />
            <span className="text-lg font-bold tracking-tight">DClaw Crisis</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600">
            <a href="#features" className="hover:text-gray-900 transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-gray-900 transition-colors">How It Works</a>
            <a href="#crisis-types" className="hover:text-gray-900 transition-colors">Crisis Types</a>
            <a href="#testimonials" className="hover:text-gray-900 transition-colors">Customers</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">Log in</Button>
            </Link>
            <Link href="/dashboard">
              <Button size="sm" className="bg-red-600 hover:bg-red-700 text-white">Go to App</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className="relative overflow-hidden bg-gradient-to-b from-gray-50 to-white pt-20 pb-28">
        <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-gray-900 via-transparent to-transparent" />
        <div className="max-w-7xl mx-auto px-6 relative">
          <motion.div
            initial="hidden"
            animate="visible"
            className="text-center max-w-4xl mx-auto"
          >
            <motion.div custom={0} variants={fadeUp} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-50 border border-red-100 text-red-700 text-xs font-semibold mb-6">
              <Zap className="w-3.5 h-3.5" />
              AI-Native Incident Command Center
            </motion.div>

            <motion.h1 custom={1} variants={fadeUp} className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
              When Crisis Hits,{" "}
              <span className="text-red-600">Chaos</span> Becomes{" "}
              <span className="text-red-600">Command</span>
            </motion.h1>

            <motion.p custom={2} variants={fadeUp} className="text-lg md:text-xl text-gray-500 leading-relaxed mb-10 max-w-2xl mx-auto">
              The first purpose-built crisis management platform for operations, legal, HR, and PR teams. Declare, coordinate, and resolve incidents with AI-powered precision.
            </motion.p>

            <motion.div custom={3} variants={fadeUp} className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/dashboard">
                <Button size="lg" className="bg-red-600 hover:bg-red-700 text-white px-8 h-12 text-base">
                  Launch Command Center
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <a href="#features">
                <Button size="lg" variant="outline" className="px-8 h-12 text-base">
                  Explore Features
                </Button>
              </a>
            </motion.div>

            <motion.div custom={4} variants={fadeUp} className="mt-12 flex items-center justify-center gap-6 text-sm text-gray-400">
              <span className="flex items-center gap-1.5"><Clock className="w-4 h-4" /> Sub-minute declaration</span>
              <span className="flex items-center gap-1.5"><Users className="w-4 h-4" /> Team-based roles</span>
              <span className="flex items-center gap-1.5"><TrendingUp className="w-4 h-4" /> Real-time metrics</span>
            </motion.div>
          </motion.div>
        </div>

        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 animate-bounce text-gray-300">
          <ChevronDown className="w-6 h-6" />
        </div>
      </section>

      {/* TRUST BANNER */}
      <section className="border-y border-gray-100 bg-white py-10">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <p className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-6">Trusted by crisis response teams at</p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12 opacity-40 grayscale">
            {["Acme Corp", "Globex", "Initech", "Massive Dynamic", "Umbrella", "Wayne Ent"].map((name) => (
              <span key={name} className="text-lg font-bold tracking-tight text-gray-900">{name}</span>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="features" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Everything You Need to Command a Crisis</h2>
            <p className="text-gray-500 text-lg">
              From the first alert to the post-mortem report, DClaw Crisis gives your team a single source of truth.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08, duration: 0.4 }}
              >
                <Card className="h-full bg-white border-gray-100 hover:border-gray-200 hover:shadow-md transition-all duration-300">
                  <CardContent className="p-6 space-y-3">
                    <div className="w-10 h-10 rounded-lg bg-gray-50 flex items-center justify-center border border-gray-100">
                      {f.icon}
                    </div>
                    <h3 className="font-semibold text-gray-900">{f.title}</h3>
                    <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how-it-works" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">How DClaw Crisis Works</h2>
            <p className="text-gray-500 text-lg">
              A simple, repeatable workflow that turns panic into process.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            {/* Connector line */}
            <div className="hidden md:block absolute top-12 left-[12.5%] right-[12.5%] h-0.5 bg-gray-100" />

            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.4 }}
                className="relative text-center"
              >
                <div className="w-16 h-16 mx-auto rounded-full bg-gray-50 border border-gray-100 flex items-center justify-center mb-4 relative z-10">
                  {step.icon}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* DASHBOARD PREVIEW */}
      <section className="py-24 bg-gradient-to-b from-gray-900 to-gray-800 text-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-semibold mb-6">
                <BarChart3 className="w-3.5 h-3.5" />
                Live Command Center
              </div>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-6">
                One Dashboard. Total Visibility.
              </h2>
              <p className="text-gray-400 text-lg leading-relaxed mb-8">
                See every active crisis, open action item, and critical alert in real time. 
                Severity breakdowns, resolution velocity, and team performance — all at a glance.
              </p>
              <ul className="space-y-4">
                {[
                  "Active crisis counter with severity heatmap",
                  "Kanban action item boards per crisis",
                  "Communication timeline with role-based filtering",
                  "Playbook-triggered auto-assignment engine",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
                    <span className="text-gray-300">{item}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-10">
                <Link href="/dashboard">
                  <Button size="lg" className="bg-white text-gray-900 hover:bg-gray-100 px-8 h-12 text-base">
                    Open Dashboard
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative"
            >
              <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-2xl overflow-hidden">
                <div className="h-8 bg-gray-700 flex items-center px-4 gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500" />
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="ml-4 text-xs text-gray-400 font-mono">DClaw Crisis — Command Center</span>
                </div>
                <div className="p-6 space-y-4">
                  {/* Mock dashboard UI */}
                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { label: "Active Crises", value: "3", color: "text-red-400" },
                      { label: "Open Actions", value: "12", color: "text-orange-400" },
                      { label: "Critical", value: "1", color: "text-red-500" },
                      { label: "Avg Resolution", value: "4.2h", color: "text-green-400" },
                    ].map((stat) => (
                      <div key={stat.label} className="bg-gray-700/50 rounded-lg p-3 border border-gray-600/50">
                        <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
                        <div className="text-xs text-gray-400 mt-1">{stat.label}</div>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-gray-700/50 rounded-lg p-3 border border-gray-600/50">
                      <div className="text-xs text-gray-400 mb-2">Severity Breakdown</div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-red-500" /><div className="h-1.5 flex-1 bg-gray-600 rounded-full overflow-hidden"><div className="h-full bg-red-500 w-[20%]" /></div><span className="text-xs text-gray-400">1</span></div>
                        <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-orange-500" /><div className="h-1.5 flex-1 bg-gray-600 rounded-full overflow-hidden"><div className="h-full bg-orange-500 w-[40%]" /></div><span className="text-xs text-gray-400">2</span></div>
                        <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-yellow-500" /><div className="h-1.5 flex-1 bg-gray-600 rounded-full overflow-hidden"><div className="h-full bg-yellow-500 w-[40%]" /></div><span className="text-xs text-gray-400">2</span></div>
                      </div>
                    </div>
                    <div className="bg-gray-700/50 rounded-lg p-3 border border-gray-600/50 space-y-2">
                      <div className="text-xs text-gray-400 mb-1">Recent Updates</div>
                      <div className="text-xs text-gray-300">"Standing up response team..."</div>
                      <div className="text-xs text-gray-300">"Alternate supplier contacted."</div>
                      <div className="text-xs text-gray-300">"Exec brief drafted for CEO."</div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CRISIS TYPES */}
      <section id="crisis-types" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Coverage for Every Crisis Type</h2>
            <p className="text-gray-500 text-lg">
              From supply chain disruptions to PR disasters — DClaw Crisis supports every category of business incident.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {crisisTypes.map((ct, i) => (
              <motion.div
                key={ct.label}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06, duration: 0.3 }}
              >
                <Card className="bg-white border-gray-100 hover:border-red-200 hover:shadow-md transition-all duration-300 cursor-default">
                  <CardContent className="p-5 flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center text-red-600">
                      {ct.icon}
                    </div>
                    <span className="font-medium text-gray-900">{ct.label}</span>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section id="testimonials" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight mb-4">Trusted by Crisis Leaders</h2>
            <p className="text-gray-500 text-lg">
              See why operations, legal, and security teams rely on DClaw Crisis when it matters most.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.12, duration: 0.4 }}
              >
                <Card className="h-full bg-gray-50 border-gray-100">
                  <CardContent className="p-6 flex flex-col h-full">
                    <div className="mb-4">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <span key={s} className="text-amber-400 text-lg">★</span>
                      ))}
                    </div>
                    <p className="text-gray-700 leading-relaxed flex-1 mb-6">"{t.quote}"</p>
                    <div>
                      <div className="font-semibold text-gray-900">{t.name}</div>
                      <div className="text-sm text-gray-500">{t.role}</div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-red-600">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-6"
          >
            Ready to Take Command?
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-red-100 text-lg md:text-xl leading-relaxed mb-10"
          >
            Join the teams replacing chaos with clarity. Launch your crisis command center in seconds.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/dashboard">
              <Button size="lg" className="bg-white text-red-600 hover:bg-gray-100 px-10 h-14 text-base font-semibold">
                Launch DClaw Crisis
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </motion.div>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4 }}
            className="text-red-200/70 text-sm mt-6"
          >
            No credit card required. Open source and free to self-host.
          </motion.p>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-gray-900 text-gray-400 py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-6 h-6 text-red-500" />
                <span className="text-lg font-bold text-white">DClaw Crisis</span>
              </div>
              <p className="text-sm leading-relaxed max-w-sm">
                AI-native Crisis & Incident Command Center built for operations, legal, HR, and PR teams who refuse to let chaos win.
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a></li>
                <li><Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
                <li><Link href="/crisis" className="hover:text-white transition-colors">Crisis Manager</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4 text-sm">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
                <li><a href="#" className="hover:text-white transition-colors">GitHub</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-sm">
            <p>© 2025 DClaw Crisis. All rights reserved.</p>
            <div className="flex items-center gap-6">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Security</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
