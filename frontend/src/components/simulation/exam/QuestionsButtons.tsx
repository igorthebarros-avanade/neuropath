import { Dispatch, SetStateAction } from "react"
import Button from "../../global/Button"

type Props = {
    currentQuestionIndex: number
    setCurrentQuestionIndex: Dispatch<SetStateAction<number>>
    currentAnswer: string
    allAnswers: string[]
    setAllAnswers: Dispatch<SetStateAction<string[]>>
}

const container = `flex items-center justify-between`
const rightButtons = `flex gap-4 items-center`

export default function QuestionsButtons(props: Props){
    function resetSimulation(){
        props.setAllAnswers(
            props.allAnswers.map(() => '')
        )

        props.setCurrentQuestionIndex(0)
    }

    function previousQuestion(){
        let newAnswers = props.allAnswers
        newAnswers[props.currentQuestionIndex] = props.currentAnswer
        props.setAllAnswers(newAnswers)
        
        props.setCurrentQuestionIndex(props.currentQuestionIndex - 1)
    }

    function submitAnswer(){
        let newAnswers = props.allAnswers
        newAnswers[props.currentQuestionIndex] = props.currentAnswer
        props.setAllAnswers(newAnswers)

        props.setCurrentQuestionIndex(props.currentQuestionIndex + 1)
    }

    return (
        <section className={container}>
            <Button isDisabled={props.currentQuestionIndex == 0} isSecondary onClick={resetSimulation}>
                <i className="ri-close-large-line"></i> Reset simulation
            </Button>

            <div className={rightButtons}>
                <Button isDisabled={props.currentQuestionIndex == 0} isSecondary onClick={previousQuestion}>
                    <i className="ri-arrow-left-long-line"></i> Previous question
                </Button>

                <Button isDisabled={!props.currentAnswer} onClick={submitAnswer}>
                    <i className="ri-check-line"></i> Submit answer
                </Button>
            </div>
        </section>
    )
}