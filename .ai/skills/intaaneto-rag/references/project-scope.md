# Project scope

## Research topic

Nghiên cứu xây dựng hệ thống E-learning trên môi trường web tích hợp giảng viên
ảo dựa trên công nghệ Trí tuệ nhân tạo.

## Objective

Create an active, interactive learning environment where an AI Tutor checks a
learner's understanding before allowing progression. Reduce lecturers' routine
work in summarizing lessons and grading basic periodic assessments.

## Required research and implementation scope

- Implement lecturer/learner authorization, course management, and academic
  document storage.
- Research extraction and normalization of PDF learning files into an AI
  knowledge base. DOCX, PPT, and PPTX uploads are outside the project target.
- Build an AI Tutor that summarizes lessons, answers grounded questions,
  evaluates understanding through dialogue, and supports interactive video.
- Track learning progress from AI-assisted assessment results.
- Produce the scientific research report and reproducible evaluation evidence.

## Expected outcomes

- A web E-learning system with the project's principal user roles and course
  workflow.
- A virtual lecturer that can present lesson summaries through voice and image.
- An AI dialogue assessment system with measured accuracy, consistency, and
  objectivity.
- Learner progress reports based on assessment outcomes.
- A scientific research report describing method, experiments, results,
  limitations, and future work.

## Core capability map

```text
Academic files
  -> extraction and normalization
  -> RAG knowledge base
  -> grounded AI Tutor
       -> question answering
       -> lesson summarization
       -> guided knowledge checks
       -> assessment evidence
  -> progress and progression rules

Approved lesson content
  -> script / TTS / avatar-video pipeline
  -> virtual lecturer presentation
```

## Priority interpretation

RAG is the backend knowledge core, but it is not the entire thesis. Complete a
measurable grounded RAG and assessment loop first. Then integrate voice/video
presentation and progress reporting around that trusted core.

The first complete research loop should demonstrate:

1. A lecturer uploads or approves lesson material.
2. The backend extracts, chunks, embeds, and indexes the material.
3. An authorized learner asks questions and receives cited answers.
4. The AI conducts a bounded knowledge check based on the same evidence.
5. The system records an explainable score/result and applies a progression rule.
6. Evaluation reports retrieval quality, answer groundedness, assessment
   consistency, latency, and relevant limitations.
