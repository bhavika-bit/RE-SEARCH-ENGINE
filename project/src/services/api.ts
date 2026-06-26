const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

export interface Project {
  project_id: string;
  topic: string;
  problem_statement: string;
  timeline: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ToolResult {
  tool: string;
  result: string;
  timestamp: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  answer: number;
  explanation: string;
}

export interface Quiz {
  questions: QuizQuestion[];
}

export interface Flashcard {
  front: string;
  back: string;
}

export interface Flashcards {
  flashcards: Flashcard[];
}

// eslint-disable-next-line prefer-const
let mockProjects: Project[] = [
  {
    project_id: 'proj_001',
    topic: 'Neural Network Optimization for Image Classification',
    problem_statement: 'How can we improve the accuracy and efficiency of image classification models using novel neural network architectures?',
    timeline: '6 months',
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    project_id: 'proj_002',
    topic: 'Climate Change Impact on Agricultural Yields',
    problem_statement: 'Modeling the effects of changing climate patterns on crop productivity in developing regions.',
    timeline: '12 months',
    created_at: '2024-02-01T14:30:00Z',
  },
];

export async function createProject(
  topic: string,
  problem_statement: string,
  timeline: string
): Promise<Project> {
  await delay(800);
  const project: Project = {
    project_id: generateId(),
    topic,
    problem_statement,
    timeline,
    created_at: new Date().toISOString(),
  };
  mockProjects.unshift(project);
  return project;
}

export async function loadAllProjects(): Promise<Project[]> {
  await delay(300);
  return [...mockProjects];
}

export async function loadProject(projectId: string): Promise<Project | null> {
  await delay(300);
  return mockProjects.find(p => p.project_id === projectId) || null;
}

export async function uploadDocuments(files: File[]): Promise<{ success: boolean; count: number }> {
  await delay(1500);
  return { success: true, count: files.length };
}

export async function indexDocuments(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _projectId: string
): Promise<{ success: boolean; message: string }> {
  await delay(2000);
  return { success: true, message: `Indexed 15 chunks from uploaded documents.` };
}

export async function sendChatMessage(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _projectId: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _message: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _history: Message[]
): Promise<Message> {
  await delay(1000);
  const responses = [
    "That's an interesting question! Based on the research context, I would suggest starting with a literature review on recent advances in this domain.",
    "The methodology you're considering aligns well with established practices. However, you might want to explore alternative approaches like transformer-based models.",
    "I found several relevant papers in the indexed documents. Would you like me to summarize the key findings?",
    "Your hypothesis seems promising. Consider validating it with empirical experiments first before diving deeper.",
    "The timeline you've proposed is realistic, but I'd recommend adding buffer time for unexpected challenges.",
  ];
  return {
    id: generateId(),
    role: 'assistant',
    content: responses[Math.floor(Math.random() * responses.length)],
    timestamp: new Date().toISOString(),
  };
}

export async function runTool(
  _projectId: string,
  toolName: string
): Promise<ToolResult> {
  await delay(2000);

  const toolResults: Record<string, string> = {
    roadmap: `## Project Roadmap\n\n### Milestones\n\n**Week 1-2: Literature Review**\n- Survey 20+ papers on the topic\n- Identify key methodologies and gaps\n- Document findings in structured format\n\n**Week 3-4: Data Preparation**\n- Collect and clean datasets\n- Perform exploratory data analysis\n- Document preprocessing pipeline\n\n**Week 5-8: Model Development**\n- Implement baseline models\n- Design novel architecture\n- Conduct initial experiments\n\n**Week 9-12: Evaluation & Iteration**\n- Run comprehensive evaluations\n- Fine-tune hyperparameters\n- Compare against SOTA\n\n**Week 13-16: Documentation**\n- Write methodology section\n- Prepare visualizations\n- Draft conclusions\n\n### Dependencies\n- Data prep must complete before modeling\n- Baseline results needed before novel architecture\n- Evaluation results required for paper writing`,

    gap_analysis: `## Research Gap Analysis\n\n### Common Themes\nMost papers focus on supervised learning approaches for this problem. There is limited exploration of unsupervised and semi-supervised methods.\n\n### Repeated Methodologies\n- CNN architectures dominate image-based tasks\n- Transformer models for NLP components\n- Ensemble methods for improved accuracy\n\n### Current Limitations\n1. **Dataset limitations**: Most studies use benchmark datasets without domain-specific data\n2. **Evaluation limitations**: Lack of cross-domain generalization testing\n3. **Deployment limitations**: Few papers address real-world deployment constraints\n\n### Missing Research Areas\n- Transfer learning from related domains\n- Few-shot learning applications\n- Uncertainty quantification\n- Model interpretability\n\n### Novelty Opportunities\n1. **Multi-modal fusion approach** (Difficulty: 7/10) - High publication potential\n2. **Self-supervised pre-training** (Difficulty: 8/10) - Medium publication potential\n3. **Domain adaptation framework** (Difficulty: 6/10) - High publication potential`,

    learning_path: `## Learning Path\n\n### Prerequisites\n- Linear algebra and calculus\n- Python programming\n- Basic machine learning concepts\n- Statistics and probability\n\n### Knowledge Graph\n\n\`\`\`\nFoundation\n├── ML Fundamentals\n│   ├── Supervised Learning\n│   ├── Unsupervised Learning\n│   └── Model Evaluation\n├── Deep Learning Basics\n│   ├── Neural Network Architecture\n│   ├── Backpropagation\n│   └── Optimization\n└── Advanced Topics\n    ├── Attention Mechanisms\n    ├── Transfer Learning\n    └── Research Methods\n\`\`\`\n\n### Weekly Learning Plan\n\n**Week 1-2**: Complete foundational ML courses\n**Week 3-4**: Study deep learning architectures\n**Week 5-6**: Read 5 key papers in the domain\n**Week 7-8**: Implement baseline paper reproduction\n\n### Practical Exercises\n1. Build a simple classifier from scratch\n2. Reproduce results from a recent paper\n3. Design and run a small experiment`,

    methodology: `## Methodology Design\n\n### Recommended Architecture\n\n\`\`\`\nInput → Preprocessing → Feature Extraction → Model → Post-processing → Output\n\`\`\`\n\n**Inputs**: Raw data (images, text, or structured data)\n**Processing**: Normalization, augmentation, tokenization\n**Model**: Hybrid CNN-Transformer architecture\n**Outputs**: Predictions with confidence scores\n\n### Technical Stack\n- **Framework**: PyTorch 2.0+\n- **Libraries**: Hugging Face Transformers, Weights & Biases\n- **Compute**: 1x A100 GPU (40GB) recommended\n\n### Risk Analysis\n| Risk | Probability | Impact | Mitigation |\n|------|-------------|--------|------------|\n| Data scarcity | Medium | High | Use augmentation, transfer learning |\n| Compute limits | Low | Medium | Optimize batch sizes, use mixed precision |\n| Convergence issues | Medium | Medium | Tune learning rate schedule |\n\n### Publication Potential\n- **Novelty**: 7/10\n- **Feasibility**: 8/10\n- **Publishability**: 7/10`,

    paper_intelligence: `## Paper Intelligence Report\n\n### Paper Comparison Matrix\n\n| Paper | Dataset | Model | Result | Strength | Weakness |\n|-------|---------|-------|--------|----------|----------|\n| Smith et al. 2023 | ImageNet | ResNet-152 | 94.2% | Strong baseline | Compute heavy |\n| Lee et al. 2024 | Custom | ViT-Large | 96.1% | SOTA results | Limited data |\n| Chen et al. 2023 | COCO | EfficientNet | 93.8% | Efficient | Lower accuracy |\n\n### Methodology Trends\n- Vision Transformers gaining popularity\n- Self-supervised pre-training becoming standard\n- Multi-scale architectures for better feature extraction\n\n### Most Influential Papers\n1. **Vaswani et al.** - "Attention is All You Need" - Foundation of transformers\n2. **Dosovitskiy et al.** - "An Image is Worth 16x16 Words" - ViT introduction\n3. **He et al.** - "Deep Residual Learning" - ResNet architecture\n\n### Reading Priority\n**Beginner**: ResNet paper, CNN fundamentals\n**Intermediate**: Vision Transformer paper\n**Advanced**: Recent SOTA papers, optimization techniques`,

    research_discovery: `## Research Discovery Report\n\n### Field Overview\nThis domain sits at the intersection of computer vision and machine learning, focusing on developing intelligent systems that can understand and reason about visual data.\n\n### Important Research Directions\n1. **Vision-Language Models** - Unifying visual and textual understanding\n2. **Efficient Architectures** - Reducing compute requirements while maintaining accuracy\n3. **Self-Supervised Learning** - Learning from unlabeled data\n4. **Multi-Task Learning** - Single models for multiple tasks\n5. **Robustness & Safety** - Ensuring reliable real-world deployment\n\n### Dataset Landscape\n\n| Dataset | Purpose | Size | Common Usage |\n|---------|---------|------|-------------|\n| ImageNet | Classification | 1.2M images | Benchmark, pre-training |\n| COCO | Detection | 330K images | Object detection, segmentation |\n| LAION | Pre-training | 5B pairs | Large-scale VLM training |\n\n### Research Ecosystem\n**Conferences**: CVPR, ICCV, NeurIPS, ICLR\n**Journals**: TPAMI, IJCV\n**Groups**: Google Brain, Meta FAIR, OpenAI`,

    mentor_review: `## Research Mentor Review\n\n### Overall Assessment\n\n| Criteria | Score (1-10) |\n|----------|-------------|\n| Clarity | 8 |\n| Novelty | 6 |\n| Feasibility | 7 |\n| Impact | 7 |\n\n### Strengths\n- Clear problem definition\n- Well-defined timeline\n- Relevant research direction with practical applications\n\n### Weaknesses\n- Novelty could be stronger\n- Risk mitigation not fully addressed\n- Limited validation strategy\n\n### Reviewer Concerns\n1. How will you differentiate from existing approaches?\n2. What datasets will you use for validation?\n3. How will you handle failure cases?\n\n### Next 5 Actions\n1. Refine novelty claim with specific differentiators\n2. Identify and secure access to necessary datasets\n3. Implement baseline for comparison\n4. Document detailed experimental design\n5. Set up project tracking and weekly milestones\n\n### Success Probability\n**70%** - Project is feasible but requires careful execution.`,

    project_summary: `## Executive Summary\nThis project aims to advance the state of the art in the specified domain through novel methodological contributions.\n\n### Problem Statement\nThe core challenge being addressed is improving accuracy and efficiency while maintaining practical applicability.\n\n### Why This Matters\n- Advances scientific understanding\n- Enables practical applications\n- Addresses existing limitations in the field\n\n### Current State of Research\nThe field has seen significant progress in recent years, with transformer-based architectures achieving state-of-the-art results. However, challenges remain in efficiency and generalization.\n\n### Proposed Solution\nA hybrid approach combining the strengths of existing methods with novel innovations in architecture and training procedures.\n\n### Expected Outcomes\n- Novel methodology with demonstrated improvements\n- Open-source implementation\n- Published research paper\n\n### Innovation Score: 7/10\n### Feasibility Score: 8/10\n\n### Elevator Pitch\nWe propose a novel approach that achieves state-of-the-art results with 40% less computational cost, making advanced techniques accessible to resource-constrained environments.`,
  };

  return {
    tool: toolName,
    result: toolResults[toolName] || `Tool "${toolName}" executed successfully. Results would be displayed here.`,
    timestamp: new Date().toISOString(),
  };
}

export async function generateQuiz(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _projectId: string
): Promise<Quiz> {
  await delay(1500);

  return {
    questions: [
      {
        question: 'What is the primary advantage of using attention mechanisms in neural networks?',
        options: [
          'They allow the model to focus on relevant parts of the input',
          'They reduce the computational cost of training',
          'They eliminate the need for labeled data',
          'They prevent overfitting automatically',
        ],
        answer: 0,
        explanation: 'Attention mechanisms enable the model to weigh different parts of the input differently, focusing computational resources on the most relevant elements.',
      },
      {
        question: 'Which of the following is NOT a common evaluation metric for classification tasks?',
        options: [
          'F1 Score',
          'Mean Squared Error',
          'Accuracy',
          'Precision',
        ],
        answer: 1,
        explanation: 'Mean Squared Error (MSE) is a regression metric, not typically used for classification tasks which use metrics like accuracy, precision, recall, and F1 score.',
      },
      {
        question: 'What is transfer learning?',
        options: [
          'Moving data between servers',
          'Using a pre-trained model on a new task',
          'Converting between file formats',
          'Distributing training across GPUs',
        ],
        answer: 1,
        explanation: 'Transfer learning involves taking a model trained on one task and adapting it to a related task, leveraging learned features to reduce training time and data requirements.',
      },
      {
        question: 'Which regularization technique randomly sets neurons to zero during training?',
        options: [
          'L1 Regularization',
          'Batch Normalization',
          'Dropout',
          'Early Stopping',
        ],
        answer: 2,
        explanation: 'Dropout randomly sets a fraction of neurons to zero during training, preventing co-adaptation and reducing overfitting.',
      },
      {
        question: 'What is the purpose of a validation set in machine learning?',
        options: [
          'To train the model parameters',
          'To test the final model performance',
          'To tune hyperparameters and prevent overfitting',
          'To store model weights',
        ],
        answer: 2,
        explanation: 'The validation set is used to evaluate model performance during training, allowing for hyperparameter tuning and early stopping to prevent overfitting.',
      },
    ],
  };
}

export async function checkQuizAnswers(quiz: Quiz, userAnswers: number[]): Promise<{
  correct: number;
  total: number;
  results: { questionIndex: number; correct: boolean; userAnswer: number }[];
}> {
  await delay(500);
  let correct = 0;
  const results = quiz.questions.map((q, i) => {
    const isCorrect = userAnswers[i] === q.answer;
    if (isCorrect) correct++;
    return { questionIndex: i, correct: isCorrect, userAnswer: userAnswers[i] };
  });
  return { correct, total: quiz.questions.length, results };
}

export async function generateFlashcards(
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _projectId: string
): Promise<Flashcards> {
  await delay(1000);

  return {
    flashcards: [
      {
        front: 'Attention Mechanism',
        back: 'A technique that allows neural networks to focus on specific parts of the input sequence by computing weighted combinations of all input elements.',
      },
      {
        front: 'Transformer',
        back: 'A neural network architecture based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Introduced in "Attention is All You Need" (2017).',
      },
      {
        front: 'Fine-tuning',
        back: 'The process of taking a pre-trained model and training it further on a smaller, task-specific dataset to adapt it to new domains or tasks.',
      },
      {
        front: 'Self-Supervised Learning',
        back: 'A training paradigm where the model learns from unlabeled data by creating supervisory signals from the data itself, such as predicting masked tokens.',
      },
      {
        front: 'Batch Normalization',
        back: 'A technique that normalizes activations in each layer to have zero mean and unit variance, reducing internal covariate shift and enabling faster training.',
      },
      {
        front: 'Gradient Descent',
        back: 'An optimization algorithm that iteratively adjusts model parameters in the direction that minimizes the loss function by computing gradients.',
      },
      {
        front: 'Overfitting',
        back: 'When a model learns the training data too well, including noise, resulting in poor generalization to new, unseen data.',
      },
      {
        front: 'Convolutional Neural Network',
        back: 'A deep learning architecture designed for processing grid-like data such as images, using convolutional layers to detect local patterns.',
      },
    ],
  };
}

export async function exportProject(projectId: string): Promise<string> {
  await delay(500);
  const project = mockProjects.find(p => p.project_id === projectId);
  const exportData = {
    metadata: project || { project_id: projectId },
    chat_history: [],
    exported_at: new Date().toISOString(),
  };
  return JSON.stringify(exportData, null, 2);
}

export async function importProject(jsonData: string): Promise<Project> {
  await delay(1000);
  const data = JSON.parse(jsonData);
  const project: Project = {
    project_id: generateId(),
    topic: data.metadata?.topic || 'Imported Project',
    problem_statement: data.metadata?.problem_statement || '',
    timeline: data.metadata?.timeline || 'Unknown',
    created_at: new Date().toISOString(),
  };
  mockProjects.unshift(project);
  return project;
}
