import apiService from "@/src/domain/services/apiService"
import { Dispatch, FormEvent, SetStateAction, useState } from "react"
import Button from "../global/Button"
import TextArea from "../global/TextArea"

type Props = {
    setQuestionAnswer: Dispatch<SetStateAction<string>>
    setShowLoading: Dispatch<SetStateAction<boolean>>
}

const button = `flex items-center justify-center mt-4 mb-8`

export default function AskForm(props: Props){
    const [question, setQuestion] = useState('')
    
    async function handleSubmit(e: FormEvent<HTMLFormElement>){
        e.preventDefault()
        props.setShowLoading(true)
        const questionAnswer = (await apiService.getAnswer(question))
        props.setQuestionAnswer(questionAnswer)
    }

    return(
        <form autoComplete="off" onSubmit={handleSubmit}>
            <TextArea label="What would you like to know about Azure Certifications?" setValue={setQuestion} value={question}/>

            <div className={button}>
                <Button isSubmit>Submit question</Button>
            </div>
        </form>
    )
}