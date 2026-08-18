# -*- coding: utf-8 -*-
# Original (not verbatim-copied) upright/reversed interpretations, written for Astrowatch's
# Tarot mode. Card-to-astrology/element/keyword attributions follow the standard Golden
# Dawn / Rider-Waite-Smith correspondence system used across virtually all tarot literature
# (facts/attributions, not any single author's protected expression). Cross-checked for
# consistency against the user-provided reference book (Liz Dean, "The Ultimate Guide to
# Tarot", Fair Winds Press) but written independently in Astrowatch's own words rather than
# reproducing that book's text, to avoid republishing copyrighted prose in this repository.

MEANINGS = {
    # ---------------- MAJOR ARCANA ----------------
    "The Fool": (
        "A fresh start beckons. Step forward with an open heart, even without every detail "
        "worked out -- naivety here is really just trust that the journey will teach you what you need.",
        "Recklessness or hesitation born of fear. A leap taken without any forethought, or an "
        "opportunity you're too afraid to take at all; slow down and look before committing.",
    ),
    "The Magician": (
        "You have every tool you need already in hand. Focus your will, align intention with "
        "action, and what you're building starts to take real shape.",
        "Scattered energy, manipulation, or talent left unused. A gap between what you say and "
        "what you actually do; be wary of trickery, including your own self-deception.",
    ),
    "The High Priestess": (
        "Trust your inner knowing over what's obvious on the surface. Secrets, intuition, and "
        "patience are at work here -- not everything is meant to be revealed yet.",
        "Disconnection from your intuition, or a secret that's causing harm by staying hidden. "
        "You may be ignoring a truth you already sense.",
    ),
    "The Empress": (
        "Abundance, nurturing, and creative growth. This is a fertile, sensory time -- for a "
        "project, a relationship, or literally new life -- so let things flourish.",
        "Creative block, neglect (of self or others), or smothering care that's become "
        "overbearing. Something that should be growing has stalled.",
    ),
    "The Emperor": (
        "Structure, authority, and steady leadership. Build something durable through discipline "
        "and clear boundaries rather than force of personality alone.",
        "Rigidity, control issues, or an abuse of authority -- yours or someone else's. Excessive "
        "control is choking out what it was meant to protect.",
    ),
    "The Hierophant": (
        "Tradition, formal learning, and shared belief. A mentor, institution, or established "
        "path offers guidance worth honoring, even if it isn't flashy.",
        "Rejecting convention, or blind conformity to it. Question inherited rules rather than "
        "following them (or breaking them) without thought.",
    ),
    "The Lovers": (
        "A meaningful choice about values and connection. Deep relationship harmony is possible "
        "when both people are honest about what they want.",
        "Misalignment, temptation, or a values conflict pulling a relationship or decision out "
        "of balance. Honesty with yourself is overdue.",
    ),
    "The Chariot": (
        "Willpower and drive carry you through opposition to a clear victory. Stay focused and "
        "keep the reins of competing forces firmly in hand.",
        "Loss of direction or self-control. Aggression, or a stalling out from internal conflict "
        "pulling you in two directions at once.",
    ),
    "Strength": (
        "Quiet, patient courage -- not force. You tame difficulty (in others or yourself) through "
        "compassion, self-control, and inner resolve.",
        "Self-doubt, or raw emotion overpowering good judgment. A loss of confidence, or forcing "
        "an issue when gentleness was called for.",
    ),
    "The Hermit": (
        "Withdrawal for the sake of insight. Step back from the noise to reflect, and let your "
        "own inner light guide the next step rather than outside opinion.",
        "Isolation that's tipped into loneliness, or refusing helpful guidance out of stubbornness. "
        "Too much time alone with your own thoughts.",
    ),
    "The Wheel of Fortune": (
        "A turning point outside your full control. Circumstances shift -- often for the better "
        "-- reminding you that change itself is the only constant.",
        "A run of bad luck, or resistance to a change that's already underway. What goes down "
        "eventually turns again, so don't lose heart.",
    ),
    "Justice": (
        "Fairness, truth, and accountability. A decision or legal matter resolves according to "
        "the facts; cause and effect are being weighed honestly.",
        "Unfairness, dishonesty, or avoiding responsibility for consequences. A decision that "
        "hasn't been thought through, or a truth being denied.",
    ),
    "The Hanged Man": (
        "A necessary pause. Surrendering control and seeing a situation from a completely "
        "different angle brings insight that action alone couldn't.",
        "Stalling, martyrdom, or resisting a pause you actually need. Delay caused by refusing "
        "to let go of a fixed point of view.",
    ),
    "Death": (
        "A genuine, often overdue ending that clears space for something new. Not literal death "
        "-- transformation that requires releasing what's already over.",
        "Resistance to necessary change, or a transition dragged out longer than it needs to be. "
        "Fear of the ending is causing more pain than the ending itself.",
    ),
    "Temperance": (
        "Balance, patience, and blending opposites into something workable. Moderation and "
        "careful timing bring healing where extremes would fail.",
        "Excess, imbalance, or impatience that undoes careful progress. Competing needs pulling "
        "apart instead of coming together.",
    ),
    "The Devil": (
        "Awareness of what's binding you -- addiction, an unhealthy attachment, or fear -- is the "
        "first step; the chains are looser than they feel.",
        "Breaking free of a restrictive pattern, or, alternatively, sinking deeper into it. A "
        "moment of choice about whether to finally let go.",
    ),
    "The Tower": (
        "Sudden, disruptive upheaval that tears down a false structure. Painful in the moment, "
        "but it clears away what was never built to last.",
        "Disaster narrowly avoided, or change resisted until it becomes unavoidable. Fear of "
        "collapse rather than the collapse itself.",
    ),
    "The Star": (
        "Hope, healing, and quiet renewal after hardship. Trust returns; inspiration flows more "
        "freely, and the worst really does seem to be over.",
        "Despair, disconnection from hope, or a creative block. Faith in the future feels harder "
        "to access right now, but it isn't gone.",
    ),
    "The Moon": (
        "Uncertainty, intuition, and things not fully visible yet. Emotions and imagination run "
        "high -- proceed carefully and don't mistake fear for fact.",
        "Confusion clearing, or, conversely, deception and anxiety intensifying. Hidden things "
        "coming to light, for better or worse.",
    ),
    "The Sun": (
        "Joy, vitality, and clear success. A genuinely positive, warm period -- confidence, good "
        "health, and recognition are well earned here.",
        "A temporary dimming of that joy -- delays or a minor setback -- but the Sun's warmth is "
        "still fundamentally on your side.",
    ),
    "Judgment": (
        "A reckoning or reawakening. Honest self-assessment leads to a second chance, a calling "
        "answered, or the past finally being put to rest.",
        "Self-doubt, harsh self-judgment, or refusing to learn from the past. An important call "
        "to change is being ignored.",
    ),
    "The World": (
        "Completion and success. A major cycle closes with a genuine sense of accomplishment, "
        "wholeness, and readiness for what comes next.",
        "Incompletion, or success delayed. Loose ends remain; something needs to be finished "
        "before the next chapter can properly begin.",
    ),

    # ---------------- MINOR ARCANA: CUPS (emotion, relationships, water) ----------------
    "Ace of Cups": ("A new wave of love, emotional openness, or creative inspiration begins.",
                     "Emotional blockage, a love that doesn't get off the ground, or bottled-up feelings."),
    "Two of Cups": ("Mutual connection and partnership -- a relationship, friendship, or reconciliation in balance.",
                     "A relationship out of sync, miscommunication, or a connection that's cooling."),
    "Three of Cups": ("Celebration among friends or family; shared joy, community, and creative collaboration.",
                       "Overindulgence, gossip, or a friendship strained by rivalry or excess."),
    "Four of Cups": ("Apathy or boredom -- an offer sits unnoticed while you're preoccupied with what's missing.",
                      "Renewed openness after a period of withdrawal, or continued stagnation if the offer is missed again."),
    "Five of Cups": ("Loss and regret take center stage, but not everything has spilled -- something remains standing.",
                      "Beginning to accept a loss and move forward, or staying stuck in what went wrong."),
    "Six of Cups": ("Nostalgia, childhood memories, and reconnecting warmly with the past or old friends.",
                     "Living too much in the past, or outgrowing a nostalgic attachment that no longer serves you."),
    "Seven of Cups": ("Many tempting options and daydreams -- exciting, but none of it is real until you choose and commit.",
                       "Clarity cutting through illusion, or continued indecision and wishful thinking."),
    "Eight of Cups": ("Walking away from something that no longer satisfies, even if it looks fine from the outside.",
                       "Fear of leaving keeping you stuck, or an aimless drifting without real direction."),
    "Nine of Cups": ("Contentment and wishes fulfilled -- a genuinely satisfying, comfortable moment.",
                      "Overindulgence, smugness, or satisfaction that's more surface-level than it appears."),
    "Ten of Cups": ("Lasting happiness, harmony at home, and emotional fulfillment shared with loved ones.",
                     "Disharmony at home or a family rift beneath an otherwise happy-looking picture."),
    "Page of Cups": ("Playful emotional news -- an invitation, a crush, or a creative idea worth exploring.",
                      "Emotional immaturity, disappointing news, or creative ideas that stay unrealized."),
    "Knight of Cups": ("A romantic offer or invitation arrives, following the heart with genuine sincerity.",
                        "An offer that isn't as sincere as it seems, or unrealistic romantic idealism."),
    "Queen of Cups": ("A deeply intuitive, compassionate presence -- emotionally attuned and quietly wise.",
                       "Emotional overwhelm, moodiness, or using empathy in a way that becomes self-sacrificing."),
    "King of Cups": ("Calm emotional mastery -- a person who leads with compassion while staying level-headed.",
                      "Moodiness hidden behind a calm exterior, or emotional manipulation."),

    # ---------------- MINOR ARCANA: PENTACLES (material world, work, body, earth) ----------------
    "Ace of Pentacles": ("A new opportunity for money, work, or health -- a solid, practical beginning.",
                          "A missed opportunity, financial setback, or a promising start that doesn't take root."),
    "Two of Pentacles": ("Juggling priorities -- money, work, or commitments -- and finding a workable rhythm.",
                          "Overcommitment and disorganization; the balancing act starts to slip."),
    "Three of Pentacles": ("Skilled teamwork and craftsmanship pay off; recognition follows genuine effort.",
                            "Poor teamwork, low standards, or work going unrecognized."),
    "Four of Pentacles": ("Holding tightly to security -- savings, property, or control -- sometimes too tightly.",
                           "Loosening the grip on money or control, or, conversely, deepening stinginess and fear of loss."),
    "Five of Pentacles": ("A period of hardship or feeling left out in the cold, materially or otherwise.",
                           "Recovery beginning after hard times, or continued financial/health worry."),
    "Six of Pentacles": ("Generosity and fair exchange -- giving or receiving help in a balanced way.",
                          "An imbalance of power in giving and receiving -- strings attached, or one-sided generosity."),
    "Seven of Pentacles": ("Patient assessment of effort already invested, and a decision about whether to keep going.",
                            "Impatience with slow progress, or wasted effort on something not worth the investment."),
    "Eight of Pentacles": ("Diligent, focused work toward mastery -- skill built through steady practice.",
                            "Sloppy work, lack of focus, or overworking without real progress to show for it."),
    "Nine of Pentacles": ("Self-sufficiency and enjoyment of what you've built -- comfort earned through your own effort.",
                           "Overwork without enjoyment, or financial setback threatening hard-won independence."),
    "Ten of Pentacles": ("Lasting wealth, legacy, and family stability built up over the long term.",
                          "Family financial conflict, or instability threatening what took generations to build."),
    "Page of Pentacles": ("Practical news about money or study -- a grounded new opportunity worth pursuing.",
                           "A missed opportunity or lack of follow-through on practical plans."),
    "Knight of Pentacles": ("Steady, methodical progress -- reliable, if slow, movement toward a material goal.",
                             "Stubbornness or stagnation; progress stalls from excessive caution."),
    "Queen of Pentacles": ("A nurturing, practical presence who manages resources -- home, money, health -- with care.",
                            "Neglect of practical matters, or smothering over-caretaking."),
    "King of Pentacles": ("Material mastery and generosity -- steady wealth built and shared wisely.",
                           "Greed, materialism, or stubborn resistance to any risk at all."),

    # ---------------- MINOR ARCANA: SWORDS (mind, conflict, communication, air) ----------------
    "Ace of Swords": ("Mental clarity and a decisive new idea cut straight through confusion.",
                       "Confusion, a decision that backfires, or clarity used carelessly, as a weapon."),
    "Two of Swords": ("An emotional stalemate -- a difficult decision deliberately avoided or postponed.",
                       "A decision finally forced, or continued avoidance that only deepens the tension."),
    "Three of Swords": ("Heartbreak and painful truth -- sorrow that, however sharp, is at least honest.",
                         "Healing beginning after grief, or wounds reopened by dwelling on old pain."),
    "Four of Swords": ("Rest and recuperation -- a deliberate pause from conflict or overwork to recover.",
                        "Restlessness despite needing rest, or burnout from refusing to stop."),
    "Five of Swords": ("Conflict with a hollow victory -- winning the argument but damaging the relationship.",
                        "Reconciliation after conflict, or continued bitterness and one-upmanship."),
    "Six of Swords": ("Moving on from a difficult period toward calmer waters, even if slowly.",
                       "Feeling stuck despite wanting to move on, or a rocky, unfinished transition."),
    "Seven of Swords": ("Strategy, secrecy, or getting away with something -- not necessarily honest, but effective.",
                         "A deception uncovered, or guilt catching up with a past act of dishonesty."),
    "Eight of Swords": ("Feeling trapped by circumstances that are, on closer look, more escapable than they seem.",
                         "Breaking free of self-imposed limitation, or continuing to feel needlessly powerless."),
    "Nine of Swords": ("Anxiety and sleepless worry -- fears looming larger in the mind than in reality.",
                        "Relief as worries ease, or anxiety deepening into despair if left unaddressed."),
    "Ten of Swords": ("A painful ending that's fully run its course -- rock bottom, and therefore also a turning point.",
                       "Recovery beginning after a hard ending, or dread of an ending that hasn't fully arrived yet."),
    "Page of Swords": ("Sharp curiosity and quick communication -- an alert mind gathering information.",
                        "Gossip, a miscommunication, or scattered thinking that jumps to conclusions."),
    "Knight of Swords": ("Fast, direct action driven by conviction -- decisive, but prone to recklessness.",
                          "Impulsiveness or aggression that outruns good judgment."),
    "Queen of Swords": ("Sharp, honest perception -- someone who sees clearly and speaks the truth without flinching.",
                         "Coldness or cutting words; honesty tipping over into harshness."),
    "King of Swords": ("Clear, authoritative judgment -- decisions grounded in logic and fair-minded truth.",
                        "Rigid, cold authority, or intellect used to manipulate rather than clarify."),

    # ---------------- MINOR ARCANA: WANDS (energy, ambition, creativity, fire) ----------------
    "Ace of Wands": ("A burst of new inspiration or opportunity -- the spark of a venture worth pursuing.",
                      "A delayed start, lost motivation, or an opportunity that fizzles before it begins."),
    "Two of Wands": ("Planning ahead with confidence -- weighing options before committing to a bigger path.",
                      "Fear of the unknown holding back a decision, or plans made without real follow-through."),
    "Three of Wands": ("Expansion and looking ahead -- early efforts start to pay off as opportunity broadens.",
                        "Delays to plans already in motion, or a lack of foresight causing setbacks."),
    "Four of Wands": ("Celebration and homecoming -- a milestone reached, stability and joy well-earned.",
                       "A celebration postponed, or instability at home disrupting an otherwise happy moment."),
    "Five of Wands": ("Competition and friction -- conflicting egos or ideas clashing, but ultimately productive.",
                       "Conflict avoided, or unresolved tension that keeps simmering beneath the surface."),
    "Six of Wands": ("A well-earned public win -- recognition and success after real effort.",
                      "Recognition delayed or withheld, or a success that turns out to be less solid than it looked."),
    "Seven of Wands": ("Standing your ground under pressure -- defending your position takes real effort but holds.",
                        "Feeling overwhelmed and giving up ground, or fighting battles that aren't worth it."),
    "Eight of Wands": ("Fast-moving news, travel, or events -- momentum picks up quickly.",
                        "Delays and frustration as fast-moving plans suddenly stall."),
    "Nine of Wands": ("Resilience after a long struggle -- wounded but still standing, guard still up.",
                       "Exhaustion or feeling under siege, defenses worn too thin to keep holding on."),
    "Ten of Wands": ("Carrying a heavy load of responsibility -- success achieved, but at real personal cost.",
                      "Setting down an unsustainable burden, or continuing to be crushed under too much weight."),
    "Page of Wands": ("Enthusiastic news or an exciting new idea, eager to be explored.",
                       "Unfocused enthusiasm, or news and ideas that don't lead anywhere yet."),
    "Knight of Wands": ("Bold, fast action driven by passion and confidence -- charging ahead toward a goal.",
                         "Impulsiveness, recklessness, or enthusiasm that burns out before the job is done."),
    "Queen of Wands": ("Warm, confident charisma -- creative energy paired with genuine determination.",
                        "Insecurity beneath the confidence, or willfulness that tips into stubbornness."),
    "King of Wands": ("Visionary, confident leadership -- inspiring others while driving ambitious plans forward.",
                       "Arrogance, impatience, or a leader who overreaches and burns bridges."),
}

if __name__ == "__main__":
    print(f"{len(MEANINGS)} original card entries defined (expect 78)")
