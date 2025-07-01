import { Dispatch, SetStateAction } from "react";
import Button from "../../global/Button";
import { useRouter } from "next/navigation";
import { ParamValue } from "next/dist/server/request/params";

type Props = {
    allAnswers: string[]
    examQuestions: any[]
    exam: ParamValue
    setCurrentQuestionIndex: Dispatch<SetStateAction<number>>
}

const buttons = `flex gap-8 items-center justify-center`

export default function FinishTest(props: Props){
    const router = useRouter()

    function reviewQuestions(){
        props.setCurrentQuestionIndex(0)
    }

    function saveResults(){
        const time = new Date()

        let attemptedQuestions = []
        for(let i = 0; i < props.examQuestions.length; i++){
            let question = props.examQuestions[i]

            question.question_number = i + 1
            question.user_answer = props.allAnswers[i]

            attemptedQuestions.push(question)
        }

        const resultsObj = {
            exam_code: props.exam,
            timestamp: time.toDateString(),
            questions_attempted: attemptedQuestions
        }

        let simulationResultsForExam = JSON.parse(
            localStorage.getItem(`simulationResults-${props.exam}`) || '[]'
        )
        simulationResultsForExam.push(resultsObj)
        localStorage.setItem(
            `simulationResults-${props.exam}`, 
            JSON.stringify(simulationResultsForExam)
        )

        router.push(`/feedback?exam=${props.exam}`)
    }

    return (
        <section>
            <div className={buttons}>
                <Button isSecondary onClick={reviewQuestions}>
                    <i className="ri-arrow-left-long-line"></i> Review questions
                </Button>

                <Button onClick={saveResults}>
                    <i className="ri-check-line"></i> Save results
                </Button>
            </div>
        </section>
    )
}