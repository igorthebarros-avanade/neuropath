import { Dispatch, SetStateAction } from "react"
import TextArea from "../../global/TextArea"
import Radio from "../../global/Radio"

type Props = {
    allAnswers: string[]
    currentQuestion: any
    currentQuestionIndex: number
    currentAnswer: string
    setCurrentAnswer: Dispatch<SetStateAction<string>>
}

const container = `mb-12`
const title = `mb-6 text-[20px]`
const answer = `pl-2`

export default function CurrentQuestion(props: Props){
    return (
        <section className={container}>
            <h2 className={title}>{props.currentQuestion.question || ''}</h2>

            <div className={answer}>
                {props.currentQuestion.type == 'yes_no' ?
                    <Radio name="currentQuestion" options={[
                        {text: 'Yes', value: 'Yes'},
                        {text: 'No', value: 'No'}
                    ]} setValue={props.setCurrentAnswer} value={props.currentAnswer}/>
                    :
                    <TextArea setValue={props.setCurrentAnswer} value={props.currentAnswer}/>
                }
            </div>
        </section>
    )
}