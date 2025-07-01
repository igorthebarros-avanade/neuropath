import Markdown from "react-markdown"

type Props = {
    answer: string
}

const title = `font-bold mb-3 text-[24px]`

export default function QuestionAnswer(props: Props){
    return (
        <>
        <h2 className={title}>AI Answer:</h2>

        <Markdown>
            {props.answer.includes('**Summary Table') ?
                props.answer.substring(0, props.answer.indexOf('**Summary Table'))
            :
                props.answer
            }
        </Markdown>
        </>
    )
}