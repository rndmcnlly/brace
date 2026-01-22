# Brace's Knowledge Wiki as Agent Skills

This document explores how Brace's knowledge wiki system (stored in the `book/` directory) relates to the concept of [Agent Skills](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/overview) from Claude's documentation.

## What are Agent Skills?

Agent Skills are structured prompts that define specific capabilities and behaviors for AI assistants. They provide specialized instructions that enable the assistant to perform particular tasks or adopt certain behaviors in well-defined contexts. Rather than having one monolithic system prompt, Agent Skills allow for modular, context-specific instructions that can be activated when needed.

Key characteristics of Agent Skills:
- **Modular**: Each skill is self-contained and focused on a specific capability
- **Contextual**: Skills are activated based on conversational context or explicit triggers
- **Composable**: Multiple skills can work together to create complex behaviors
- **Maintainable**: Individual skills can be updated without affecting others

## Brace's Knowledge Wiki as a Skill System

Brace implements a sophisticated skill system through its knowledge wiki, which functions as a collection of dynamically-loaded Agent Skills. The wiki pages in the `book/` directory serve as modular instruction sets that are retrieved and injected into the conversation context as needed.

### Architecture of Brace's Skill System

**Discovery Phase**: At the start of every conversation, Brace loads:
1. Instructions for using the `⟨wiki _.md⟩` command syntax
2. A complete list of all available wiki page filenames (the "skill catalog")
3. The README.md page (the "base skill" providing foundational instructions)

**Dynamic Activation**: When the assistant needs specialized knowledge:
1. The assistant includes a `⟨wiki filename.md⟩` command in its response
2. The auto-continue mechanism triggers to process the command
3. The specified wiki page is loaded and injected into the context
4. The assistant continues with the newly-available instructions

This architecture mirrors the Agent Skills paradigm where skills are:
- **Discovered**: The initial skill catalog provides awareness of available capabilities
- **Selected**: The assistant chooses which skills to activate based on user needs
- **Applied**: Skills are loaded into context and shape subsequent behavior

### Types of Skills in Brace's Wiki

The wiki implements several categories of skills:

#### 1. Interface Skills (`interface/` directory)
These skills guide the assistant in using specific features of the Brace system:

- **Profile Builder** (`interface/profile_builder.md`): A structured interview protocol for gathering user preferences. This skill transforms the assistant into a focused interviewer with specific questions and output formats.
- **Voice Interaction** (`interface/voice_interaction.md`): Instructions for supporting voice-based conversations
- **Non-English Conversations** (`interface/non-english_conversations.md`): Guidelines for multilingual support
- **Submitting Chat Transcripts** (`interface/submitting_chat_transcripts.md`): Procedures for Canvas LMS integration

These mirror the "Tool Use" aspect of Agent Skills, where the assistant learns to interact with external systems and APIs.

#### 2. Content Skills (`content/` directory)
These skills provide domain-specific knowledge:

- **Code Smells** (`content/smells.md`): Specialized knowledge about software quality issues

This represents domain expertise that can be injected when relevant to the conversation, similar to how Agent Skills provide specialized knowledge domains.

#### 3. Pedagogical Skills (`pedagogy/` directory)
These skills implement educational methodologies:

- **Bloom Quiz Format** (`pedagogy/bloom.md`): A complete instructional framework for conducting learning assessments based on Bloom's Taxonomy

This is a sophisticated example of a behavioral skill that completely reshapes how the assistant interacts with students, guiding them through a structured educational activity with specific question types, feedback patterns, and assessment rubrics.

#### 4. Meta-Skills (`README.md`, `self-knowledge.md`)
These provide overarching context and self-awareness:

- **README.md**: Foundational context about the course, staff, and general behavioral guidelines
- **self-knowledge.md**: Information about the Brace system itself for meta-conversations

These establish the baseline personality and contextual awareness, similar to how a system prompt establishes core behaviors in traditional Agent Skills implementations.

### Advantages of Brace's Wiki-Based Skill System

**1. Transparency and Maintainability**
Unlike traditional Agent Skills that might be stored in application code or databases, Brace's skills are plain Markdown files in a version-controlled repository. Course staff can:
- Edit skills directly in GitHub or GitBook
- Track changes over time with git history
- Collaborate on skill development through pull requests
- See the complete skill set at a glance

**2. Dynamic Updates**
The wiki files are re-read during each chat completion request, meaning skill updates are immediately available without system restarts. This allows course staff to:
- Fix errors in real-time
- Add new skills mid-semester
- Adjust pedagogical approaches based on student feedback
- Respond to emerging course needs

**3. Intelligent Resource Management**
By loading skills on-demand rather than pre-loading everything, Brace optimizes token usage:
- Only relevant skills consume context window space
- The assistant can access a large skill library without overwhelming the context
- Conversation length remains manageable even with many available skills

**4. Explicit Skill Activation**
The `⟨wiki _.md⟩` syntax makes skill activation transparent:
- Students can see when specialized knowledge is being retrieved
- The auto-continue mechanism ensures smooth skill integration
- Debugging is easier because skill loads are visible in the conversation

**5. Structured Knowledge Organization**
The directory structure (`interface/`, `content/`, `pedagogy/`) provides clear categorization:
- Skills are organized by purpose
- New skills can be added to appropriate categories
- The SUMMARY.md file acts as a navigable skill index

### Comparison with Traditional Agent Skills

| Aspect | Traditional Agent Skills | Brace's Wiki Skills |
|--------|------------------------|---------------------|
| **Storage** | Application code or database | Version-controlled Markdown files |
| **Activation** | Implicit or tool-based | Explicit wiki command syntax |
| **Visibility** | Often opaque to end users | Transparent through command syntax |
| **Updates** | Require redeployment | Live updates without restart |
| **Authoring** | Requires technical knowledge | Editable by course staff in GitBook |
| **Organization** | Varies by implementation | File system hierarchy |
| **Context Management** | Pre-loaded or lazy-loaded | On-demand loading with auto-continue |

### Educational Applications

Brace's implementation is particularly well-suited for educational contexts:

**Adaptive Instruction**: The assistant can select appropriate skills based on student needs. For example, it might load the Bloom Quiz skill when a student asks about taking a quiz, or the Code Smells skill when reviewing their programming assignment.

**Personalized Support**: The Profile Builder skill enables students to customize their experience, while the system can still access specialized pedagogical skills when needed.

**Pedagogical Consistency**: Skills like the Bloom Quiz format ensure that educational activities follow proven frameworks consistently across all interactions.

**Rapid Iteration**: Instructors can refine teaching approaches by editing wiki pages based on what works in practice, without needing technical support.

### Technical Implementation Insights

The auto-continue mechanism is crucial to Brace's skill system:
```
1. Assistant generates response ending with ⟨wiki filename.md⟩
2. Message completes and user sees the streaming response
3. Auto-continue automatically triggers
4. System processes all ⟨wiki _.md⟩ commands in assistant messages
5. Wiki pages are loaded and injected into context
6. Assistant continues generating with new instructions available
```

This creates a seamless experience where skill activation feels natural rather than mechanical. The assistant can "think" about what information it needs, request it, and then continue with enhanced capabilities—much like a human expert consulting reference materials.

## Lessons for Agent Skill Design

Brace's implementation offers several insights for designing Agent Skill systems:

**1. Make Skills Self-Documenting**
Each wiki page contains complete instructions, not just data. This makes skills portable and understandable in isolation.

**2. Provide Skill Discovery Mechanisms**
The initial load of all filenames allows the assistant to know what skills are available, enabling intelligent skill selection.

**3. Support Progressive Skill Loading**
Not everything needs to be loaded upfront. Brace demonstrates that on-demand loading can be both efficient and user-friendly.

**4. Enable Non-Technical Authoring**
By using Markdown and GitBook, Brace makes skill authoring accessible to instructors without requiring programming skills.

**5. Design for Observability**
The explicit `⟨wiki _.md⟩` syntax makes the system's behavior transparent, aiding both debugging and user trust.

**6. Structure for Scale**
The directory organization and SUMMARY.md index help manage complexity as the skill library grows.

## Conclusion

Brace's knowledge wiki system represents an elegant implementation of the Agent Skills concept, specifically optimized for educational use cases. By treating each wiki page as a loadable skill module, Brace achieves:

- **Modularity**: Each wiki page is an independent, focused capability
- **Contextuality**: Skills are loaded only when needed
- **Composability**: Multiple wiki pages can work together in a single conversation
- **Maintainability**: Plain-text Markdown files in version control

The system demonstrates that Agent Skills don't require complex infrastructure—they can be implemented with simple file-based storage, explicit activation commands, and thoughtful integration with the conversation flow. This approach makes advanced AI assistant capabilities accessible to educators and course designers without requiring deep technical expertise.

For anyone building similar systems, Brace provides a valuable reference implementation showing how to create maintainable, transparent, and effective skill systems using straightforward technologies and clear design principles.
