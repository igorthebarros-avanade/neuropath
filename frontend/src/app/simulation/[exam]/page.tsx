'use client'
import PageTitle from "@/src/components/global/PageTitle"
import CurrentQuestion from "@/src/components/simulation/exam/CurrentQuestion"
import ExamProgressBar from "@/src/components/simulation/exam/ExamProgressBar"
import FinishTest from "@/src/components/simulation/exam/FinishTest"
import QuestionsButtons from "@/src/components/simulation/exam/QuestionsButtons"
import { useParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"

export default function page(){
    const router = useRouter()
    const {exam} = useParams()

    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
    const [examQuestions, setExamQuestions] = useState<any[]>([])
    const [currentQuestion, setCurrentQuestion] = useState<any>()
    const [currentAnswer, setCurrentAnswer] = useState('')
    const [allAnswers, setAllAnswers] = useState<string[]>([])

    useEffect(() => {
        const questions: any[] = JSON.parse(localStorage.getItem(`generatedQuestions-${exam}`) || '[]')

        if(questions.length > 0){
            setExamQuestions(questions)
        }else{
            router.push('/')
        }

        const answers = questions.map(() => '')
        setAllAnswers(answers)
    }, [])

    useEffect(() => {
        setCurrentQuestion(examQuestions[currentQuestionIndex])
        setCurrentAnswer(allAnswers[currentQuestionIndex])
    }, [examQuestions, currentQuestionIndex])

    return (
        <>
        <PageTitle text={`${exam} Exam Simulation`}/>

        <ExamProgressBar currentIndex={currentQuestionIndex} questionsNumber={examQuestions.length}/>

        {currentQuestion && currentQuestionIndex < examQuestions.length ?
            <>
            <CurrentQuestion allAnswers={allAnswers} currentQuestion={currentQuestion} currentQuestionIndex={currentQuestionIndex} currentAnswer={currentAnswer} setCurrentAnswer={setCurrentAnswer}/>
            <QuestionsButtons allAnswers={allAnswers} currentAnswer={currentAnswer} currentQuestionIndex={currentQuestionIndex} setAllAnswers={setAllAnswers} setCurrentQuestionIndex={setCurrentQuestionIndex}/>
            </>
        : <></>}

        {currentQuestionIndex >= examQuestions.length ?
            <FinishTest allAnswers={allAnswers} exam={exam} examQuestions={examQuestions}  setCurrentQuestionIndex={setCurrentQuestionIndex}/>
        : <></>}
        </>
    )
}