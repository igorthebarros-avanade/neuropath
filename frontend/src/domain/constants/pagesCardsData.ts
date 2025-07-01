import PageCardData from "../types/PageCardData";

const pagesCardsData: PageCardData[] = [
    {
        description: 'Start by generating questions for your desired certification, the AI will generate the given amount of questions based on the real weight of each subject there is in the exam.',
        link: '/questions',
        title: 'Generate Diagnostic Questions'
    },
    {
        description: 'After generating the questions, simulate a test answering them, and see in practice the difficulty level you will find in the exam.',
        link: '/simulation',
        title: 'Conduct Simulation'
    },
    {
        description: 'Get feedback for your simulation, knowing the performance you had in general, and under each subject. All your answers will be evaluated, and given a brief description for the correct answer.',
        link: '/feedback',
        title: 'Feedback'
    },
    {
        description: 'Ask the AI anything you want or need to know about Azure Certifications, and get even more familiar with this whole ecosystem.',
        link: '/ask',
        title: 'Ask a Question'
    }
]

export default pagesCardsData